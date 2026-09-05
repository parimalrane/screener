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

# Dynamically import all strategy modules
for _, module_name, _ in pkgutil.iter_modules(strategies.__path__):
    importlib.import_module(f"strategies.{module_name}")

# ---------------------------------------------------------
# 1. UNIVERSE SELECTION
# ---------------------------------------------------------
def get_sp500_tickers() -> list[str]:
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(io.StringIO(response.text))
        tickers = tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
        return sorted(list(set(tickers)))
    except Exception as e:
        print(f"Fallback triggered ({e}). Using liquid tech tickers.")
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "AVGO", "NFLX"]

# ---------------------------------------------------------
# 2. STOCK EVALUATION
# ---------------------------------------------------------
def evaluate_stock(ticker: str) -> list[dict]:
    results = []
    try:
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False, auto_adjust=True)
        if df_daily.empty or len(df_daily) < 250:
            return results

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        if len(df_monthly) < 30 or len(df_weekly) < 35:
            return results

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
# 3. RUNNER & PERSISTENCE
# ---------------------------------------------------------
def run_scan():
    tickers = get_sp500_tickers()
    total = len(tickers)
    active_screens = list(SCREENER_REGISTRY.keys())
    print(f"Loaded {len(active_screens)} screener(s): {active_screens}")
    print(f"Scanning {total} tickers...")

    all_matches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(evaluate_stock, t): t for t in tickers}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            completed += 1
            res = future.result()
            if res:
                all_matches.extend(res)
                for item in res:
                    print(f"-> Match: [{item['screener_name']}] {item['stock']} (${item['closing_price']})")
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} scanned...")

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