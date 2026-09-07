import concurrent.futures
import importlib
import io
import os
import pkgutil
import pandas as pd
import requests
import yfinance as yf

import strategies
from registry import SCREENER_REGISTRY
import config
import threading

DATA_DIR = "data"
IGNORE_FILE = "ignored_tickers.txt"
os.makedirs(DATA_DIR, exist_ok=True)

ignore_lock = threading.Lock()

def get_ignored_tickers() -> set:
    if os.path.exists(IGNORE_FILE):
        with open(IGNORE_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def add_to_ignore_list(ticker: str):
    with ignore_lock:
        # Extra check to prevent duplicate writes during threading
        current = get_ignored_tickers()
        if ticker not in current:
            with open(IGNORE_FILE, "a") as f:
                f.write(f"{ticker}\n")

# Dynamically import all strategy modules
for _, module_name, _ in pkgutil.iter_modules(strategies.__path__):
    importlib.import_module(f"strategies.{module_name}")

# ---------------------------------------------------------
# 1. UNIVERSE SELECTION
# ---------------------------------------------------------
def get_all_tickers() -> dict:
    try:
        import glob
        files = glob.glob("*_stocks.csv")
        files.sort()
        target_file = files[-1] if files else "stocks_universe.csv"
        
        print(f"Loading universe from: {target_file}")
        df = pd.read_csv(target_file)
        
        ticker_col = "Ticker" if "Ticker" in df.columns else df.columns[0]
        zacks_col = "Zacks Rank" if "Zacks Rank" in df.columns else None
        
        ignored = get_ignored_tickers()
        ticker_data = {}
        
        for _, row in df.iterrows():
            t = str(row[ticker_col]).strip()
            if t in ignored or t.lower() == "nan" or not t:
                continue
                
            rank = None
            if zacks_col and pd.notna(row[zacks_col]):
                try:
                    rank = int(float(row[zacks_col]))
                except ValueError:
                    pass
                    
            # Strictly ignore any stock that doesn't have a valid 1-5 rank
            if rank not in [1, 2, 3, 4, 5]:
                continue
                    
            ticker_data[t] = rank

        return ticker_data
        
    except Exception as e:
        print(f"Error reading universe: {e}")
        return {"AAPL": None, "MSFT": None}

# ---------------------------------------------------------
# 3. STOCK EVALUATION (Strategy Only)
# ---------------------------------------------------------
def evaluate_stock(ticker: str, zacks_rank: int, bulk_update: pd.DataFrame = None) -> list[dict]:
    results = []
    try:
        hist_file = os.path.join(DATA_DIR, f"cache_{ticker}.csv")
        df_daily = pd.DataFrame()

        # 1. Try to load local history
        if os.path.exists(hist_file):
            try:
                df_daily = pd.read_csv(hist_file, index_col="Date", parse_dates=True)
            except Exception:
                pass
        
        # 2. Extract recent bulk data for this ticker (fast update)
        new_data = pd.DataFrame()
        if bulk_update is not None and not bulk_update.empty:
            try:
                if isinstance(bulk_update.columns, pd.MultiIndex):
                    # Safely extract regardless of whether yfinance groups by (Price, Ticker) or (Ticker, Price)
                    if ticker in bulk_update.columns.get_level_values(1):
                        new_data = bulk_update.xs(ticker, axis=1, level=1)
                    elif ticker in bulk_update.columns.get_level_values(0):
                        new_data = bulk_update.xs(ticker, axis=1, level=0)
                else:
                    new_data = bulk_update
                new_data = new_data.dropna(how="all")
            except Exception:
                pass
        
        # 3. Combine or download full history if missing
        previous_latest_date = df_daily.index[-1] if not df_daily.empty else None
        
        if df_daily.empty:
            # First time run (or corrupted CSV): pull full 10y history for EMA stability
            df_daily = yf.download(ticker, period="10y", interval="1d", progress=False, auto_adjust=True)
            if df_daily.empty:
                # Automatically blacklist delisted/dead tickers so we never query them again
                add_to_ignore_list(ticker)
                return results
                
            if isinstance(df_daily.columns, pd.MultiIndex):
                df_daily.columns = df_daily.columns.get_level_values(0)
            df_daily.index.name = "Date"
            df_daily.to_csv(hist_file)
        elif not new_data.empty:
            # We have local history and new delta data to compress and merge
            df_daily = pd.concat([df_daily, new_data])
            df_daily = df_daily[~df_daily.index.duplicated(keep="last")].sort_index()
            df_daily = df_daily.tail(2500)  # Retain ~10 years exactly
            df_daily.to_csv(hist_file)
        
        if df_daily.empty or len(df_daily) < 250:
            return results

        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        if len(df_monthly) < 30 or len(df_weekly) < 35:
            return results

        # Global Volatility Check (Drop boring stocks early)
        recent_adr = ((df_daily["High"] - df_daily["Low"]) / df_daily["Close"] * 100).tail(20).mean()
        if recent_adr < getattr(config, "MIN_ADR_PERCENT", 0):
            return results

        # Calculate dates correctly because stock.history uses timezone-aware datetime index
        market_date = df_daily.index[-1].strftime("%Y%m%d")
        close_price = round(float(df_daily["Close"].iloc[-1]), 2)

        for screen_name, screen_func in SCREENER_REGISTRY.items():
            # Check the config file to see if the user manually disabled this strategy
            if not getattr(config, "STRATEGIES", {}).get(screen_name, True):
                continue
                
            # Zacks Rank Filter Logic
            name_lower = screen_name.lower()
            if zacks_rank is not None:
                if "bullish" in name_lower and zacks_rank in [4, 5]:
                    continue
                if "bearish" in name_lower and zacks_rank in [1, 2]:
                    continue
                
            try:
                res = screen_func(df_daily, df_weekly, df_monthly)
                is_hit = False
                tags = ""
                
                if isinstance(res, tuple):
                    is_hit, tags = res
                else:
                    is_hit = res
                    
                if is_hit:
                    row = {
                        "marketdate": market_date,
                        "screener_name": screen_name,
                        "stock": ticker
                    }
                    if isinstance(tags, dict):
                        row.update(tags)
                    elif isinstance(tags, str):
                        row["tags"] = tags
                    results.append(row)
            except Exception:
                continue

    except Exception:
        return results

    return results

# ---------------------------------------------------------
# 4. RUNNER & PERSISTENCE
# ---------------------------------------------------------
def run_scan():
    tickers_dict = get_all_tickers()
    tickers = list(tickers_dict.keys())
    total = len(tickers)
    
    active_screens = [name for name in SCREENER_REGISTRY.keys() if getattr(config, "STRATEGIES", {}).get(name, True)]
    
    names_map = {
        "Bullish_TS_Daily": "BU_TSD", "Bullish_TS_Hourly": "BU_TSH",
        "Bullish_MOM": "BU_MOM", "Bullish_Swing": "BU_SWG",
        "Bearish_TS_Daily": "BE_TSD", "Bearish_TS_Hourly": "BE_TSH",
        "Bearish_MOM": "BE_MOM", "Bearish_Swing": "BE_SWG"
    }
    short_screens = [names_map.get(name, name) for name in active_screens]
    print(f"Loaded {len(short_screens)} active screener(s): {short_screens}")
    
    # Check if network update is even necessary by comparing cache to SPY's latest date
    needs_update = True
    if total > 0:
        hist_file = os.path.join(DATA_DIR, f"cache_{tickers[0]}.csv")
        if os.path.exists(hist_file):
            try:
                df_test = pd.read_csv(hist_file, index_col="Date", parse_dates=True)
                spy = yf.download("SPY", period="5d", progress=False)
                if spy.empty:
                    print("Yahoo Finance API rate limit detected. Bypassing massive bulk download to protect cache...")
                    needs_update = False
                elif not df_test.empty:
                    # If local cache matches or exceeds Yahoo's latest market tick, skip massive download
                    if df_test.index[-1] >= spy.index[-1]:
                        needs_update = False
            except Exception:
                pass
                
    if needs_update:
        # bulk update without verbose progress bars
        bulk_update = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=True)
    else:
        bulk_update = None

    all_matches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(evaluate_stock, t, tickers_dict[t], bulk_update): t for t in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res:
                all_matches.extend(res)

    csv_file = "screener_results.csv"

    if all_matches:
        df_new = pd.DataFrame(all_matches)
        
        # Rename 'tags' to 'Probability' if it exists in the dataframe
        if 'tags' in df_new.columns:
            df_new.rename(columns={'tags': 'Probability'}, inplace=True)

        names_map = {
            "Bullish_TS_Daily": "BU_TSD",
            "Bullish_TS_Hourly": "BU_TSH",
            "Bullish_MOM": "BU_MOM",
            "Bullish_Swing": "BU_SWG",
            "Bearish_TS_Daily": "BE_TSD",
            "Bearish_TS_Hourly": "BE_TSH",
            "Bearish_MOM": "BE_MOM",
            "Bearish_Swing": "BE_SWG"
        }
        df_new["screener_name"] = df_new["screener_name"].replace(names_map)

        prob_map = {"High": "H", "Medium": "M"}
        if "Probability" in df_new.columns:
            df_new["Probability"] = df_new["Probability"].replace(prob_map)

        def get_prob_rank(val):
            if pd.isna(val): return 2
            s = str(val).lower()
            if s in ["high", "h"]: return 0
            if s in ["medium", "m"]: return 1
            return 2
            
        def get_strategy_rank(val):
            if pd.isna(val): return 99
            s = str(val).upper()
            if "TSD" in s: return 0
            if "TSH" in s: return 1
            if "MOM" in s: return 2
            if "SWG" in s: return 3
            return 99
            
        df_new["is_bull"] = df_new["screener_name"].str.startswith("BU")
        df_new["prob_rank"] = df_new.get("Probability", pd.Series(dtype=str)).apply(get_prob_rank)
        df_new["strategy_rank"] = df_new["screener_name"].apply(get_strategy_rank)
        
        # Sort hierarchy: Bullish first -> Strategy (TS, MOM, SWING) -> Probability (H, M) -> Ticker
        df_new = df_new.sort_values(by=["is_bull", "strategy_rank", "prob_rank", "stock"], ascending=[False, True, True, True])
        df_new = df_new.drop(columns=["is_bull", "prob_rank", "strategy_rank"])
        
        print("\n" + "=" * 80)
        print("                               NEW MATCHES                               ")
        print("=" * 80)
        print(df_new.to_string(index=False))

        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            try:
                df_existing = pd.read_csv(csv_file, dtype={"marketdate": str})
                
                # If CSV is corrupted (e.g. Git conflict markers), start fresh
                if "screener_name" not in df_existing.columns:
                    raise ValueError("Corrupt CSV header")
                    
                # Ensure historic runs map tags to Probability and update to short names
                if 'tags' in df_existing.columns and 'Probability' not in df_existing.columns:
                    df_existing.rename(columns={'tags': 'Probability'}, inplace=True)
                df_existing["screener_name"] = df_existing["screener_name"].replace(names_map)
                if "Probability" in df_existing.columns:
                    df_existing["Probability"] = df_existing["Probability"].replace(prob_map)
                    
                # Erase all previous entries for the current market date to ensure a clean overwrite
                current_date = df_new["marketdate"].iloc[0]
                df_existing = df_existing[df_existing["marketdate"] != current_date]
                
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                
                # Re-sort the final master csv historically and by strategy / probability
                df_combined["is_bull"] = df_combined["screener_name"].str.startswith("BU")
                df_combined["prob_rank"] = df_combined.get("Probability", pd.Series(dtype=str)).apply(get_prob_rank)
                df_combined["strategy_rank"] = df_combined.get("screener_name", pd.Series(dtype=str)).apply(get_strategy_rank)
                
                df_combined = df_combined.sort_values(
                    by=["marketdate", "is_bull", "strategy_rank", "prob_rank", "stock"], 
                    ascending=[False, False, True, True, True]
                )
                df_combined = df_combined.drop(columns=["is_bull", "prob_rank", "strategy_rank"])
                
                df_combined.to_csv(csv_file, index=False)
            except Exception as e:
                print(f"Warning: Rebuilding corrupted database... ({e})")
                df_new.to_csv(csv_file, index=False)
        else:
            df_new.to_csv(csv_file, index=False)

        print(f"\nSaved to {csv_file}")
        
        # -----------------------------------------------------
        # TRADINGVIEW WATCHLIST EXPORT BUILDER
        # -----------------------------------------------------
        print("\n" + "=" * 80)
        print("                      TRADINGVIEW WATCHLIST EXPORT                       ")
        print("=" * 80)
        
        # df_new is theoretically already sorted in the exact strategy hierarchy needed
        for strategy in df_new["screener_name"].unique():
            tickers = df_new[df_new["screener_name"] == strategy]["stock"].unique().tolist()
            if tickers:
                ticker_string = ",".join(tickers)
                print(f"###{strategy},{ticker_string},")
                
        print("=" * 80 + "\n")
        
    else:
        print("\nNo matches found today across any registered screeners.")
        if not os.path.exists(csv_file):
            pd.DataFrame(columns=["marketdate", "screener_name", "stock", "tags"]).to_csv(csv_file, index=False)

if __name__ == "__main__":
    run_scan()