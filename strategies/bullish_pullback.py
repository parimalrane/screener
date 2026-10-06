import pandas as pd
import pandas_ta as ta

from asta_conditions import (
    is_macd_pco,
    is_bbdnc,
    is_bkp
)

def _macd_above_zero(df: pd.DataFrame) -> bool:
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 1: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    return float(macd_df[macd_col].iloc[-1]) > 0.0

def scan_Bullish_Pullback(monthly_df: pd.DataFrame, weekly_df: pd.DataFrame, daily_df: pd.DataFrame) -> bool:
    """
    Bullish Pullback Scanner:
    Finds deep pullbacks into major moving averages on the daily chart 
    while preserving robust, untainted macro momentum on larger timeframes.
    """
    if len(weekly_df) < 35 or len(daily_df) < 50:
        return False

    # --- MONTHLY ---
    # Bypass monthly constraints for recent IPOs lacking enough data to build a valid Monthly MACD
    if len(monthly_df) >= 35:
        if not (is_macd_pco(monthly_df) and _macd_above_zero(monthly_df)):
            return False
            
        rsi_m = ta.rsi(monthly_df["Close"], length=14)
        if rsi_m is None or rsi_m.iloc[-1] <= 50:
            return False
            
        sma20_m = ta.sma(monthly_df["Close"], length=20)
        if sma20_m is None or monthly_df["Close"].iloc[-1] <= sma20_m.iloc[-1]:
            return False
            
        if not is_bbdnc(monthly_df):
            return False

    # --- WEEKLY ---
    if not (is_macd_pco(weekly_df) and _macd_above_zero(weekly_df)):
        return False
        
    rsi_w = ta.rsi(weekly_df["Close"], length=14)
    if rsi_w is None or rsi_w.iloc[-1] <= 50:
        return False
        
    sma20_w = ta.sma(weekly_df["Close"], length=20)
    if sma20_w is None or weekly_df["Close"].iloc[-1] <= sma20_w.iloc[-1]:
        return False
        
    if not is_bbdnc(weekly_df):
        return False

    # --- DAILY ---
    sma21_d = ta.sma(daily_df["Close"], length=21)
    sma50_d = ta.sma(daily_df["Close"], length=50)
    if sma21_d is None or sma50_d is None:
        return False
    
    close_today = daily_df["Close"].iloc[-1]
    close_yest = daily_df["Close"].iloc[-2]
    
    # 1. Price piercing below 21 or 50 SMA exactly on today's candle
    # It must be BELOW the SMA today, and it must have been ABOVE or EQUAL to the SMA yesterday
    pierced_21 = (close_today < sma21_d.iloc[-1]) and (close_yest >= sma21_d.iloc[-2])
    pierced_50 = (close_today < sma50_d.iloc[-1]) and (close_yest >= sma50_d.iloc[-2])
    
    if not (pierced_21 or pierced_50):
        return False
        
    # 2. RSI > 40
    rsi_d = ta.rsi(daily_df["Close"], length=14)
    if rsi_d is None or rsi_d.iloc[-1] <= 40:
        return False
        
    return True
