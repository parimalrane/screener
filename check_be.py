import pandas as pd
import pandas_ta as ta
import os

def run_debug():
    hist_file = os.path.join("data", "cache_BE.csv")
    if not os.path.exists(hist_file):
        print(f"File not found: {hist_file}")
        return
        
    df_daily = pd.read_csv(hist_file, index_col="Date", parse_dates=True)
    sma50 = ta.sma(df_daily["Close"], length=50)
    
    prev_close = df_daily["Close"].iloc[-2]
    prev_sma = sma50.iloc[-2]
    curr_close = df_daily["Close"].iloc[-1]
    curr_sma = sma50.iloc[-1]
    
    with open("be_sma.txt", "w") as f:
        f.write(f"Yesterday BE Close: {prev_close:.4f}, 50 SMA: {prev_sma:.4f}\n")
        f.write(f"Today BE Close: {curr_close:.4f}, 50 SMA: {curr_sma:.4f}\n")

if __name__ == "__main__":
    run_debug()
