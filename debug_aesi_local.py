import pandas as pd
import pandas_ta as ta
import os

def run_debug():
    hist_file = os.path.join("data", "cache_AESI.csv")
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
    
    print(f"\n--- 1. BASE METRICS ---")
    print(f"Price > 10: {current_close > 10} ({current_close:.2f})")
    
    sma_vol_20 = df_daily["Volume"].tail(20).mean()
    print(f"20-day Avg Vol > 1M: {sma_vol_20 > 1_000_000} ({sma_vol_20:,.0f})")
    print(f"Current Vol > 20-day Avg: {current_vol > sma_vol_20} ({current_vol:,.0f} > {sma_vol_20:,.0f})")
    
    recent_adr = ((df_daily["High"] - df_daily["Low"]) / df_daily["Close"] * 100).tail(20).mean()
    print(f"ADR > 4%: {recent_adr > 4.0} ({recent_adr:.2f}%)")
    
    print(f"\n--- 2. CROSSOVER & CANDLE ---")
    sma50 = ta.sma(df_daily["Close"], length=50)
    prev_close = df_daily["Close"].iloc[-2]
    prev_sma50 = sma50.iloc[-2]
    curr_sma50 = sma50.iloc[-1]
    
    crossed_up = prev_close <= prev_sma50 and current_close > curr_sma50
    print(f"Crossed 50 SMA Today: {crossed_up}")
    print(f"  -> Yesterday: Close {prev_close:.2f} | 50SMA {prev_sma50:.2f}")
    print(f"  -> Today:     Close {current_close:.2f} | 50SMA {curr_sma50:.2f}")
    
    total_range = current_high - current_low
    body_range = current_close - current_open
    body_pct = (body_range / total_range) if total_range > 0 else 0
    print(f"Solid Bullish Candle (>50% body): {body_pct >= 0.50} ({body_pct*100:.1f}%)")
    
    print(f"\n--- 3. RSI ---")
    rsi_d = ta.rsi(df_daily["Close"], length=14).iloc[-1]
    rsi_w = ta.rsi(df_weekly["Close"], length=14).iloc[-1]
    print(f"Daily RSI > 40: {rsi_d > 40} ({rsi_d:.1f})")
    print(f"Weekly RSI > 40: {rsi_w > 40} ({rsi_w:.1f})")
    
    print(f"\n--- 4. BOLLINGER BANDS ---")
    bb_d = ta.bbands(df_daily["Close"], length=20, std=2.0)
    bbl_d = bb_d.iloc[:, 0]
    bbu_d = bb_d.iloc[:, 2]
    
    d_lower_rising_or_flat = bbl_d.iloc[-1] >= bbl_d.iloc[-2]
    d_upper_rising = bbu_d.iloc[-1] > bbu_d.iloc[-2]
    print(f"Daily BB (Lower flat/up OR Upper up): {d_lower_rising_or_flat or d_upper_rising}")
    print(f"  -> Lower Band: {bbl_d.iloc[-2]:.2f} -> {bbl_d.iloc[-1]:.2f} (Rising/Flat: {d_lower_rising_or_flat})")
    print(f"  -> Upper Band: {bbu_d.iloc[-2]:.2f} -> {bbu_d.iloc[-1]:.2f} (Rising: {d_upper_rising})")
    
    bb_w = ta.bbands(df_weekly["Close"], length=20, std=2.0)
    bbl_w = bb_w.iloc[:, 0]
    bbu_w = bb_w.iloc[:, 2]
    
    w_upper_flat_or_declining = bbu_w.iloc[-1] <= bbu_w.iloc[-2]
    w_lower_declining = bbl_w.iloc[-1] < bbl_w.iloc[-2]
    weekly_bb_str = "Passed"
    if w_upper_flat_or_declining and w_lower_declining:
        weekly_bb_str = "Failed"
    print(f"Weekly BB (If Upper flat/down -> Lower NOT down): {weekly_bb_str}")
    print(f"  -> Upper Band: {bbu_w.iloc[-2]:.2f} -> {bbu_w.iloc[-1]:.2f} (Flat/Down: {w_upper_flat_or_declining})")
    print(f"  -> Lower Band: {bbl_w.iloc[-2]:.2f} -> {bbl_w.iloc[-1]:.2f} (Declining: {w_lower_declining})")

if __name__ == "__main__":
    run_debug()
