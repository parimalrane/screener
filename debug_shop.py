import pandas as pd
from strategies.bullish_catalyst import check
import os

ticker = "SHOP"
hist_file = f"c:/screener/data/cache_{ticker}.csv"
df_daily = pd.read_csv(hist_file, index_col="Date", parse_dates=True)

print("TAIL OF DF DAILY:")
print(df_daily.tail(5))

current_close = df_daily['Close'].iloc[-1]
prev_close = df_daily['Close'].iloc[-2]
pct_change = (current_close - prev_close) / prev_close
print(f"Current: {current_close}, Prev: {prev_close}, Pct Change: {pct_change}")

