import yfinance as yf
import pandas as pd
from strategies.bullish_catalyst import check
from asta_conditions import (
    is_bbdnc, is_rsi_above, is_macd_up, is_solid_candle
)

# Use PENG as an example, since grep showed PENG was flagged previously
ticker = "PENG"
df = yf.download(ticker, period="2y", interval="1d", progress=False)
if df.empty:
    print("No data")
    exit()

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
df_weekly = df.resample("W-FRI").agg(resample_rules).dropna()
df_monthly = df.resample("ME").agg(resample_rules).dropna()

print(f"Daily Len: {len(df)}")
print(f"Weekly Len: {len(df_weekly)}")
print(f"Monthly Len: {len(df_monthly)}")

if len(df) < 50 or len(df_weekly) < 20:
    print("Failed: Length constraints")

if len(df_monthly) >= 20:
    print("Monthly BBDNC:", is_bbdnc(df_monthly))
    print("Monthly MACD UP:", is_macd_up(df_monthly))

print("Weekly BBDNC:", is_bbdnc(df_weekly))
print("Weekly RSI > 40:", is_rsi_above(df_weekly, 40))

current_close = df['Close'].iloc[-1]
current_open = df['Open'].iloc[-1]
current_volume = df['Volume'].iloc[-1]
prev_close = df['Close'].iloc[-2]
avg_volume_20 = df['Volume'].rolling(window=20).mean().iloc[-2]

print("Price > 1:", not (pd.isna(current_close) or current_close <= 1.0))
pct_change = (current_close - prev_close) / prev_close
print("Change > 10%:", not (pd.isna(pct_change) or pct_change < 0.10), f"({pct_change*100:.2f}%)")
print("Vol > 1M:", not (pd.isna(current_volume) or current_volume < 1_000_000), current_volume)
print("RVol > 3:", not (pd.isna(avg_volume_20) or avg_volume_20 <= 0 or current_volume < (avg_volume_20 * 3)), f"({current_volume/avg_volume_20 if avg_volume_20 > 0 else 0:.2f})")
print("Solid Candle:", is_solid_candle(df, direction='bullish'))
