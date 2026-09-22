import pandas as pd
df = pd.read_csv('data/cache_EE.csv', index_col='Date', parse_dates=True)
print(df.tail(3))
print("Pct change:", (df['Close'].iloc[-1] - df['Close'].iloc[-2])/df['Close'].iloc[-2])
