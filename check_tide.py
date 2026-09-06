import pandas as pd
import pandas_ta as ta
import os

def run_debug():
    hist_file = os.path.join("data", "cache_AESI.csv")
    if not os.path.exists(hist_file): return
        
    df_daily = pd.read_csv(hist_file, index_col="Date", parse_dates=True)
    resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
    
    bb_w = ta.bbands(df_weekly["Close"], length=20, std=2)
    bbu_w = bb_w.iloc[:, 2]
    bbl_w = bb_w.iloc[:, 0]
    
    w_upper_rising = bbu_w.iloc[-1] > bbu_w.iloc[-2]
    w_lower_declining = bbl_w.iloc[-1] < bbl_w.iloc[-2]
    
    print("\n--- AESI WEEKLY TIDE CHECK ---")
    print(f"Weekly Upper BB Rising: {w_upper_rising} ({bbu_w.iloc[-2]:.2f} -> {bbu_w.iloc[-1]:.2f})")
    print(f"Weekly Lower BB Declining: {w_lower_declining} ({bbl_w.iloc[-2]:.2f} -> {bbl_w.iloc[-1]:.2f})")

if __name__ == "__main__":
    run_debug()
