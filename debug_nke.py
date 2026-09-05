import yfinance as yf
import pandas as pd
import pandas_ta as ta

def run_debug():
    print("Testing NKE...")
    df_daily = yf.download("NKE", period="3y", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)

    resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
    df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

    macd_m = ta.macd(df_monthly["Close"], fast=12, slow=26, signal=9)
    rsi_m = ta.rsi(df_monthly["Close"], length=14)
    sma_m = ta.sma(df_monthly["Close"], length=20)
    
    cond1 = macd_m["MACD_12_26_9"].iloc[-1] < macd_m["MACDs_12_26_9"].iloc[-1]
    cond2 = rsi_m.iloc[-1] < 40
    cond3 = df_monthly["Close"].iloc[-1] < sma_m.iloc[-1]
    
    print(f"Monthly: MACD<Sig={cond1}, RSI={rsi_m.iloc[-1]:.2f}<40?={cond2}, Price<SMA={cond3}")

    macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
    rsi_w = ta.rsi(df_weekly["Close"], length=14)
    cond4 = macd_w["MACD_12_26_9"].iloc[-1] > macd_w["MACDs_12_26_9"].iloc[-1]
    cond5 = rsi_w.iloc[-1] < 60
    print(f"Weekly: MACD>Sig={cond4}, RSI={rsi_w.iloc[-1]:.2f}<60?={cond5}")

    macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
    stoch_d = ta.stoch(df_daily["High"], df_daily["Low"], df_daily["Close"], k=14, d=3, smooth_k=3)
    
    cond6 = macd_d["MACD_12_26_9"].iloc[-1] < macd_d["MACD_12_26_9"].iloc[-2]
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    cond7 = (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
    cond8 = k.iloc[-3] > 70
    
    print(f"Daily: MACD down={cond6}, Stoch Cross={cond7} (K={k.iloc[-1]:.2f}, D={d.iloc[-1]:.2f}, yK={k.iloc[-2]:.2f}, yD={d.iloc[-2]:.2f}), Overbought 2d ago={cond8} (2dK={k.iloc[-3]:.2f})")

if __name__ == "__main__":
    run_debug()
