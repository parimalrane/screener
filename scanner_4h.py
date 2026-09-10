import os
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import concurrent.futures
import warnings

warnings.filterwarnings('ignore')

UNIVERSE_FILE = "20260904_stocks.csv"
RESULTS_FILE = "screener_4h_results.csv"

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
                ticker = str(row[ticker_col]).strip()
                if not ticker or ticker.lower() == 'nan': continue
                
                try:
                    rank = int(float(row[zacks_col]))
                    # Bullish pool: Zacks Rank 1 (Strong Buy) and 2 (Buy)
                    if rank in [1, 2]:
                        bullish_list.append(ticker)
                    # Bearish pool: Zacks Rank 4 (Sell) and 5 (Strong Sell)
                    elif rank in [4, 5]:
                        bearish_list.append(ticker)
                except:
                    pass
                    
        return bullish_list, bearish_list
    except Exception as e:
        print("Error loading universe:", e)
        return [], []

def evaluate_stock(ticker, direction):
    # direction is either "BU" or "BE"
    try:
        df_daily = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df_daily.empty: return None
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)
            
        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        if len(df_weekly) < 30: return None
        
        close_w = df_weekly["Close"]
        sma_20 = ta.sma(close_w, length=20)
        macd_df = ta.macd(close_w, fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(close_w, length=14)
        
        if sma_20 is None or macd_df is None or rsi_w is None: return None
        
        macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
        sig_col = [c for c in macd_df.columns if c.startswith("MACDs_")][0]
        
        # --- WEEKLY DIRECTIONAL CHECKS ---
        if direction == "BU":
            if close_w.iloc[-1] < sma_20.iloc[-1]: return None
            if macd_df[macd_col].iloc[-1] <= macd_df[sig_col].iloc[-1]: return None
            if rsi_w.iloc[-1] <= 40: return None
        else: # "BE"
            if close_w.iloc[-1] > sma_20.iloc[-1]: return None
            if macd_df[macd_col].iloc[-1] >= macd_df[sig_col].iloc[-1]: return None
            if rsi_w.iloc[-1] >= 60: return None

        # --- 4 HOUR CHECKS ---
        df_1h = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df_1h.empty: return None
        if isinstance(df_1h.columns, pd.MultiIndex):
            df_1h.columns = df_1h.columns.get_level_values(0)
            
        # Group into AM (<=12:30) and PM (>12:30) blocks to create Two 4H candles per day
        df_1h['DateOnly'] = df_1h.index.date
        df_1h['Session'] = df_1h.index.hour <= 12  
        df_4h = df_1h.groupby(['DateOnly', 'Session']).agg(resample_rules).dropna().sort_index()
        
        if len(df_4h) < 20: return None
        
        stoch_d = ta.stoch(df_4h["High"], df_4h["Low"], df_4h["Close"], k=14, d=3, smooth_k=3)
        if stoch_d is None or len(stoch_d) < 3: return None
        
        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]
        
        # --- 4 HOUR DIRECTIONAL CHECKS ---
        if direction == "BU":
            # Was < 20 recently, and just crossed UP
            extreme = (k.iloc[-2] < 20) or (k.iloc[-3] < 20)
            if not extreme: return None
            crossed = (k.iloc[-1] > d.iloc[-1]) and (k.iloc[-2] <= d.iloc[-2])
            if not crossed: return None
            screen_name = "BU_4OS"
            
        else:
            # Was > 80 recently, and just crossed DOWN
            extreme = (k.iloc[-2] > 80) or (k.iloc[-3] > 80)
            if not extreme: return None
            crossed = (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
            if not crossed: return None
            screen_name = "BE_4OS"
            
        return {
            "marketdate": df_daily.index[-1].strftime("%Y%m%d"),
            "screener_name": screen_name,
            "stock": ticker,
            "Latest_Price": round(df_daily["Close"].iloc[-1], 2),
            "4H_Stoch_K": round(k.iloc[-1], 2),
            "4H_Stoch_D": round(d.iloc[-1], 2)
        }
        
    except Exception:
        return None

import sys

def main():
    mode = "BOTH"
    if len(sys.argv) > 1:
        mode = sys.argv[1].upper()
        
    print(f"= Starting Optimized 4-Hour Tracker (Mode: {mode}) =")
    bullish_tickers, bearish_tickers = get_tickers_by_rank()
    
    results = []
    
    # Process Bullish
    if mode in ["BU", "BOTH"] and bullish_tickers:
        print(f"Processing BU_4OS on {len(bullish_tickers)} Zacks Rank 1 & 2 stocks...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tick = {executor.submit(evaluate_stock, t, "BU"): t for t in bullish_tickers}
            for future in concurrent.futures.as_completed(future_to_tick):
                res = future.result()
                if res:
                    print(f"{res['stock']}")
                    results.append(res)
                    
    # Process Bearish
    if mode in ["BE", "BOTH"] and bearish_tickers:
        print(f"\nProcessing BE_4OS on {len(bearish_tickers)} Zacks Rank 4 & 5 stocks...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tick = {executor.submit(evaluate_stock, t, "BE"): t for t in bearish_tickers}
            for future in concurrent.futures.as_completed(future_to_tick):
                res = future.result()
                if res:
                    print(f"{res['stock']}")
                    results.append(res)
                    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["screener_name", "stock"])
        
        # Decide output filename based on execution type
        out_file = RESULTS_FILE
        if mode == "BU": out_file = "screener_4h_BU_results.csv"
        if mode == "BE": out_file = "screener_4h_BE_results.csv"
            
        df_res.to_csv(out_file, index=False)
        print(f"\nPROCESS COMPLETE. Saved {len(df_res)} matches to {out_file}")
    else:
        print("\nPROCESS COMPLETE. No stocks matched the 4-Hour conditions today.")

if __name__ == '__main__':
    main()
