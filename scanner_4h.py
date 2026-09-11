import os
import sys
import pkgutil
import importlib
import concurrent.futures
import pandas as pd
import yfinance as yf
import logging

warnings = __import__("warnings")
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

import strategies
from registry import SCREENER_4H_REGISTRY

# Dynamically import all strategy modules (the 4H decorator ensures we only run 4H ones)
for _, module_name, _ in pkgutil.iter_modules(strategies.__path__):
    importlib.import_module(f"strategies.{module_name}")

UNIVERSE_FILE = "data/20260904_stocks.csv"
RESULTS_FILE = "output/screener_4h_results.csv"

def get_tickers_by_rank():
    # Returns (bullish_tickers_list, bearish_tickers_list)
    try:
        df = pd.read_csv(UNIVERSE_FILE)
        ticker_col = "Ticker" if "Ticker" in df.columns else df.columns[0]
        zacks_col = "Zacks Rank" if "Zacks Rank" in df.columns else None
        
        bullish_list = []
        bearish_list = []
        
        if zacks_col:
            for _, row in df.iterrows():
                ticker = str(row[ticker_col]).strip().replace('.', '-')
                if not ticker or ticker.lower() == 'nan': continue
                
                try:
                    rank = int(float(row[zacks_col]))
                    if rank in [1, 2]: bullish_list.append(ticker)
                    elif rank in [4, 5]: bearish_list.append(ticker)
                except:
                    pass
                    
        return bullish_list, bearish_list
    except Exception as e:
        print("Error loading universe:", e)
        return [], []

def fetch_data(ticker):
    """Downloads required arrays for 4H Strategies"""
    try:
        df_daily = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df_daily.empty: return None, None
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)
            
        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        
        df_1h = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df_1h.empty: return df_weekly, None
        if isinstance(df_1h.columns, pd.MultiIndex):
            df_1h.columns = df_1h.columns.get_level_values(0)
            
        df_1h['DateOnly'] = df_1h.index.date
        df_1h['Session'] = df_1h.index.hour <= 12  
        df_4h = df_1h.groupby(['DateOnly', 'Session']).agg(resample_rules).dropna().sort_index()
        
        return df_weekly, df_4h
    except Exception:
        return None, None

def evaluate_stock(ticker, screeners_to_run):
    try:
        df_weekly, df_4h = fetch_data(ticker)
        if df_weekly is None or df_4h is None: return []
        
        matches = []
        for name, func in screeners_to_run.items():
            if func(df_4h, df_weekly):
                matches.append({
                    "marketdate": df_4h.index[-1][0].strftime("%Y%m%d"),
                    "screener_name": name,
                    "stock": ticker
                })
        return matches
    except Exception:
        return []

def main():
    mode = "BOTH"
    if len(sys.argv) > 1:
        mode = sys.argv[1].upper()
        
    print(f"= Starting Clean Architecture 4-Hour Engine (Mode: {mode}) =")
    
    # Identify which strategies to route
    bullish_screens = {k: v for k, v in SCREENER_4H_REGISTRY.items() if k.startswith("BU")}
    bearish_screens = {k: v for k, v in SCREENER_4H_REGISTRY.items() if k.startswith("BE")}
    
    bullish_tickers, bearish_tickers = get_tickers_by_rank()
    results = []
    
    # Process Bullish Route
    if mode in ["BU", "BOTH"] and bullish_tickers and bullish_screens:
        print(f"Routing {len(bullish_tickers)} Zacks [1/2] stocks to: {list(bullish_screens.keys())}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tick = {executor.submit(evaluate_stock, t, bullish_screens): t for t in bullish_tickers}
            for future in concurrent.futures.as_completed(future_to_tick):
                res = future.result()
                for match in res:
                    print(f"{match['stock']}")
                    results.append(match)
                    
    # Process Bearish Route
    if mode in ["BE", "BOTH"] and bearish_tickers and bearish_screens:
        print(f"\nRouting {len(bearish_tickers)} Zacks [4/5] stocks to: {list(bearish_screens.keys())}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tick = {executor.submit(evaluate_stock, t, bearish_screens): t for t in bearish_tickers}
            for future in concurrent.futures.as_completed(future_to_tick):
                res = future.result()
                for match in res:
                    print(f"{match['stock']}")
                    results.append(match)
                    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["screener_name", "stock"])
        
        out_file = RESULTS_FILE
        if mode == "BU": out_file = "output/screener_4h_BU_results.csv"
        if mode == "BE": out_file = "output/screener_4h_BE_results.csv"
            
        df_res.to_csv(out_file, index=False)
        print(f"\nPROCESS COMPLETE. Saved {len(df_res)} matches to {out_file}")
    else:
        print("\nPROCESS COMPLETE. No stocks matched intraday strategies.")

if __name__ == '__main__':
    main()
