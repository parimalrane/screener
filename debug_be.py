import pandas as pd
import pandas_ta as ta
import os

def run_debug():
    hist_file = os.path.join("data", "cache_BE.csv")
    if not os.path.exists(hist_file):
        print(f"File not found: {hist_file}")
        return
        
    df_daily = pd.read_csv(hist_file, index_col="Date", parse_dates=True)
    
    # Base prep
    resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
    
    current_close = df_daily["Close"].iloc[-1]
    current_open = df_daily["Open"].iloc[-1]
    current_high = df_daily["High"].iloc[-1]
    current_low = df_daily["Low"].iloc[-1]
    current_vol = df_daily["Volume"].iloc[-1]
    
    sma50 = ta.sma(df_daily["Close"], length=50)
    prev_close = df_daily["Close"].iloc[-2]
    prev_sma50 = sma50.iloc[-2]
    curr_sma50 = sma50.iloc[-1]
    
    print(f"\n--- BE METRICS ---")
    print(f"Price: {current_close:.2f} (Yesterday: {prev_close:.2f})")
    print(f"50 SMA: {curr_sma50:.2f} (Yesterday: {prev_sma50:.2f})")
    
    body_pct = ((current_close - current_open) / (current_high - current_low)) if current_high != current_low else 0
    print(f"Green Candle? {current_close > current_open} | Body Pct: {body_pct*100:.1f}%")
    
    bb_d = ta.bbands(df_daily["Close"], length=20, std=2.0)
    bbl_d = bb_d.iloc[:, 0]
    bbu_d = bb_d.iloc[:, 2]
    print(f"Daily BB: Lower {bbl_d.iloc[-2]:.2f}->{bbl_d.iloc[-1]:.2f} | Upper {bbu_d.iloc[-2]:.2f}->{bbu_d.iloc[-1]:.2f}")

if __name__ == "__main__":
    run_debug()
