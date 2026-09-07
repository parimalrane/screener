import pandas as pd
from strategies.bullish_ts_daily import check
from asta_conditions import *
import warnings
warnings.filterwarnings('ignore')

print('Fetching WDC from parquet...')
df = pd.read_parquet('market_data_cache.parquet')
df_d = df[df['Ticker'] == 'WDC'].copy()
df_d.set_index('Date', inplace=True)
df_d.sort_index(inplace=True)

df_w = df_d.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
df_m = df_d.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

print('-----------------------')
print('MONTHLY (Tide)')
print('MACD_PCO:', is_macd_pco(df_m))
print('RSI > 60:', is_rsi_above(df_m, 60))
print('Price > 20 SMA:', is_price_above_sma(df_m, 20))

print('\nWEEKLY (Wave)')
print('MACD_NCO:', is_macd_nco(df_w))
print('RSI > 40:', is_rsi_above(df_w, 40))

print('\nDAILY (Ripple)')
print('MACD Rising:', is_macd_rising(df_d))
print('Stoch Buy Crossover:', is_stochastic_buy(df_d, strict_crossover=True))

import pandas_ta as ta
stoch_d = ta.stoch(df_d["High"], df_d["Low"], df_d["Close"], k=14, d=3, smooth_k=3)
if stoch_d is not None:
    print("\nRecent Stochastic values on Daily:")
    print(stoch_d.tail(5))

print('\nOVERALL RESULT:', check(df_d, df_w, df_m))
