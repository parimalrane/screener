import pandas as pd
import pandas_ta as ta
from registry import register_screener

@register_screener("Bearish_TS_Daily")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    try:
        # -----------------------------------------------------
        # Monthly Checks
        # -----------------------------------------------------
        macd_m = ta.macd(df_monthly["Close"], fast=12, slow=26, signal=9)
        rsi_m = ta.rsi(df_monthly["Close"], length=14)
        sma_m = ta.sma(df_monthly["Close"], length=20)
        
        if macd_m is None or rsi_m is None or sma_m is None:
            return False

        # Monthly Macd Line(26,12,9) Less than Monthly Macd Signal(26,12,9)
        cond1 = macd_m["MACD_12_26_9"].iloc[-1] < macd_m["MACDs_12_26_9"].iloc[-1]
        
        # Monthly Rsi(14) Less than Number 40
        cond2 = rsi_m.iloc[-1] < 40
        
        # Monthly Close Less than Monthly Sma(Monthly Close, 20)
        cond3 = df_monthly["Close"].iloc[-1] < sma_m.iloc[-1]
        
        if not (cond1 and cond2 and cond3):
            return False

        # -----------------------------------------------------
        # Weekly Checks
        # -----------------------------------------------------
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        
        if macd_w is None or rsi_w is None:
            return False

        # Weekly Macd Line(26,12,9) Greater than Weekly Macd Signal(26,12,9)
        cond4 = macd_w["MACD_12_26_9"].iloc[-1] > macd_w["MACDs_12_26_9"].iloc[-1]
        
        # Weekly Rsi(14) Less than Number 60
        cond5 = rsi_w.iloc[-1] < 60
        
        if not (cond4 and cond5):
            return False

        # -----------------------------------------------------
        # Daily Checks
        # -----------------------------------------------------
        macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
        stoch_d = ta.stoch(df_daily["High"], df_daily["Low"], df_daily["Close"], k=14, d=3, smooth_k=3)
        
        if macd_d is None or stoch_d is None:
            return False

        # Daily Macd Line(26,12,9) Less than 1 day ago Macd Line(26,12,9)
        cond6 = macd_d["MACD_12_26_9"].iloc[-1] < macd_d["MACD_12_26_9"].iloc[-2]
        
        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]
        
        # Daily Slow Stochastic %K(14,3) Crossed below Daily Slow Stochastic %D(14,3)
        cond7 = (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
        
        # 2 days ago Slow Stochastic %K(14,3) Greater than Number 70
        cond8 = k.iloc[-3] > 70

        return cond6 and cond7 and cond8

    except Exception:
        return False
