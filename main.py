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
def get_all_tickers() -> list[str]:
    try:
        df = pd.read_csv("stocks_universe.csv")
        base_tickers = pd.Series(df.iloc[:, 0]).dropna().astype(str).tolist()
        ignored = get_ignored_tickers()
        return [t for t in base_tickers if t not in ignored]
    except Exception as e:
        print(f"Error reading universe: {e}")
        return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "AMD", "NFLX"]

# ---------------------------------------------------------
# 3. STOCK EVALUATION (Strategy Only)
# ---------------------------------------------------------
def evaluate_stock(ticker: str, bulk_update: pd.DataFrame = None) -> list[dict]:
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
            # First time run (or corrupted CSV): pull full 3y history
            df_daily = yf.download(ticker, period="3y", interval="1d", progress=False, auto_adjust=True)
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
            df_daily = df_daily.tail(750)  # Retain ~3 years
            df_daily.to_csv(hist_file)
        
        if df_daily.empty or len(df_daily) < 250:
            return results

        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        if len(df_monthly) < 30 or len(df_weekly) < 35:
            return results

        # Calculate dates correctly because stock.history uses timezone-aware datetime index
        market_date = df_daily.index[-1].strftime("%Y%m%d")
        close_price = round(float(df_daily["Close"].iloc[-1]), 2)

        for screen_name, screen_func in SCREENER_REGISTRY.items():
            try:
                if screen_func(df_daily, df_weekly, df_monthly):
                    results.append({
                        "marketdate": market_date,
                        "screener_name": screen_name,
                        "stock": ticker,
                        "closing_price": close_price
                    })
            except Exception:
                continue

    except Exception:
        return results

    return results

# ---------------------------------------------------------
# 4. RUNNER & PERSISTENCE
# ---------------------------------------------------------
def run_scan():
    tickers = get_all_tickers()
    total = len(tickers)
    active_screens = list(SCREENER_REGISTRY.keys())
    print(f"Loaded {len(active_screens)} screener(s): {active_screens}")
    
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
        future_to_ticker = {executor.submit(evaluate_stock, t, bulk_update): t for t in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res:
                all_matches.extend(res)

    csv_file = "screener_results.csv"

    if all_matches:
        df_new = pd.DataFrame(all_matches)
        print("\n" + "=" * 50)
        print("NEW MATCHES")
        print("=" * 50)
        print(df_new.to_string(index=False))

        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            df_existing = pd.read_csv(csv_file, dtype={"marketdate": str})
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["marketdate", "screener_name", "stock"], keep="last", inplace=True)
            df_combined.to_csv(csv_file, index=False)
        else:
            df_new.to_csv(csv_file, index=False)

        print(f"\nSaved to {csv_file}")
    else:
        print("\nNo matches found today across any registered screeners.")
        if not os.path.exists(csv_file):
            pd.DataFrame(columns=["marketdate", "screener_name", "stock", "closing_price"]).to_csv(csv_file, index=False)

if __name__ == "__main__":
    run_scan()