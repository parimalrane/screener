import pandas as pd
import pandas_ta as ta
from registry import register_screener

@register_screener("Bearish_TS_Hourly")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    """
    Setup screener mapping to a Weekly Bearish Base and Daily upwards Bounce (Pullback).
    (Hourly downwards trigger is evaluated manually by the trader).
    """
    try:
        # -----------------------------------------------------
        # Bearish Macro Trend (Monthly)
        # -----------------------------------------------------
        if len(df_monthly) < 25:
            return False
            
        bb_m = ta.bbands(df_monthly["Close"], length=20, std=2)
        rsi_m = ta.rsi(df_monthly["Close"], length=14)
        sma_m = ta.sma(df_monthly["Close"], length=20)
        
        if bb_m is None or rsi_m is None or sma_m is None:
            return False
            
        bbl_m = bb_m.iloc[:, 0]  # Lower Band
        
        # Monthly BBDC (Lower BB is Challenged/Dropping)
        if bbl_m.iloc[-1] >= bbl_m.iloc[-2]:
            return False
            
        # Monthly RSI < 40
        if rsi_m.iloc[-1] >= 40:
            return False
            
        # Monthly Price < 20 SMA
        if df_monthly["Close"].iloc[-1] >= sma_m.iloc[-1]:
            return False

        # -----------------------------------------------------
        # Bearish Base Trend (Weekly)
        # -----------------------------------------------------
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        sma_w = ta.sma(df_weekly["Close"], length=20)
        
        if macd_w is None or rsi_w is None or sma_w is None:
            return False

        # Weekly MACD below signal
        cond1 = macd_w["MACD_12_26_9"].iloc[-1] < macd_w["MACDs_12_26_9"].iloc[-1]
        
        # Weekly RSI < 40 (severe macro downtrend)
        cond2 = rsi_w.iloc[-1] < 40
        
        # Weekly Price below 20-week SMA
        cond3 = df_weekly["Close"].iloc[-1] < sma_w.iloc[-1]
        
        if not (cond1 and cond2 and cond3):
            return False

        # -----------------------------------------------------
        # Bullish Pullback Bounce State (Daily)
        # -----------------------------------------------------
        macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        
        if macd_d is None or rsi_d is None:
            return False

        # Daily MACD line bouncing Upwards (greater than signal)
        cond4 = macd_d["MACD_12_26_9"].iloc[-1] > macd_d["MACDs_12_26_9"].iloc[-1]
        
        # Daily RSI safely < 60 (failed to cross into true bullish territory)
        cond5 = rsi_d.iloc[-1] < 60
        
        if not (cond4 and cond5):
            return False

        # If it passes the Weekly structural bleed and the Daily upward retracement,
        # it is formally staged for an intraday (Hourly) short execution!
        return True

    except Exception:
        return False
