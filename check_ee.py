import yfinance as yf
import pandas as pd
from asta_conditions import is_bbdnc, is_rsi_above

ticker = "EE"
df = yf.download(ticker, period="5y", interval="1d", progress=False, auto_adjust=True)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
df_weekly = df.resample("W-FRI").agg(resample_rules).dropna()
df_monthly = df.resample("ME").agg(resample_rules).dropna()

print(f"--- Data for {ticker} ---")
current_close = df['Close'].iloc[-1]
prev_close = df['Close'].iloc[-2]
pct_change = (current_close - prev_close) / prev_close
current_vol = df['Volume'].iloc[-1]
avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-2]
rvol = current_vol / avg_vol_20 if avg_vol_20 else 0

print(f"Close: {current_close:.2f} (>{1}) -> {'PASS' if current_close > 1 else 'FAIL'}")
print(f"Change: {pct_change*100:.2f}% (>{10}%) -> {'PASS' if pct_change > 0.10 else 'FAIL'}")
print(f"Volume: {current_vol:,.0f} (>1M) -> {'PASS' if current_vol > 1000000 else 'FAIL'}")
print(f"RVOL: {rvol:.2f}x (>2x) (Avg Vol: {avg_vol_20:,.0f}) -> {'PASS' if rvol >= 2 else 'FAIL'}")

if len(df_monthly) >= 20:
    print(f"Monthly BBDNC: {'PASS' if is_bbdnc(df_monthly) else 'FAIL'}")
else:
    print("Monthly: SKIPPED (IPO < 20 months)")

print(f"Weekly BBDNC: {'PASS' if is_bbdnc(df_weekly) else 'FAIL'}")

import pandas_ta as ta
rsi_weekly = ta.rsi(df_weekly['Close'], length=14)
rsi_val = rsi_weekly.iloc[-1] if rsi_weekly is not None and not rsi_weekly.empty else 0
print(f"Weekly RSI: {rsi_val:.2f} (>40) -> {'PASS' if is_rsi_above(df_weekly, 40) else 'FAIL'}")
