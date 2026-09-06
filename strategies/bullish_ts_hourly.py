import pandas as pd
import pandas_ta as ta
from registry import register_screener

@register_screener("Bullish_TS_Hourly")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    """
    Setup screener mapping to a Weekly Base and Daily Pullback.
    (Hourly trigger is evaluated manually by the trader).
    """
    try:
        # -----------------------------------------------------
        # Base Trend (Weekly)
        # -----------------------------------------------------
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        sma_w = ta.sma(df_weekly["Close"], length=20)
        
        if macd_w is None or rsi_w is None or sma_w is None:
            return False

        # Weekly MACD crossed up
        cond1 = macd_w["MACD_12_26_9"].iloc[-1] > macd_w["MACDs_12_26_9"].iloc[-1]
        
        # Weekly RSI > 60
        cond2 = rsi_w.iloc[-1] > 60
        
        # Weekly Price above 20-week SMA
        cond3 = df_weekly["Close"].iloc[-1] > sma_w.iloc[-1]
        
        if not (cond1 and cond2 and cond3):
            return False

        # -----------------------------------------------------
        # Pullback State (Daily)
        # -----------------------------------------------------
        macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        
        if macd_d is None or rsi_d is None:
            return False

        # Daily MACD line cooling off (lower than signal)
        cond4 = macd_d["MACD_12_26_9"].iloc[-1] < macd_d["MACDs_12_26_9"].iloc[-1]
        
        # Daily RSI safely elevated > 40 (trend is still intact despite pullback)
        cond5 = rsi_d.iloc[-1] > 40
        
        if not (cond4 and cond5):
            return False

        # If it passes both the Weekly structural uptrend and the Daily pullback status,
        # it is formally staged for an intraday (Hourly) entry pattern!
        return True

    except Exception:
        return False
