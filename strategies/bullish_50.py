import pandas as pd
import pandas_ta as ta
import numpy as np
from registry import register_screener

@register_screener("Bullish_50")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    try:
        # Require enough data for 50 SMA and 20 BB
        if len(df_daily) < 55 or len(df_weekly) < 25:
            return False

        current_close = df_daily["Close"].iloc[-1]
        current_open = df_daily["Open"].iloc[-1]
        current_high = df_daily["High"].iloc[-1]
        current_low = df_daily["Low"].iloc[-1]
        current_vol = df_daily["Volume"].iloc[-1]

        # -----------------------------------------------------
        # Base Filters (Volume, ADR)
        # -----------------------------------------------------
        sma_vol_20 = df_daily["Volume"].tail(20).mean()

        # Volume greater than 20-day average
        if current_vol <= sma_vol_20:
            return False

        # Daily ADR% > 4%
        recent_adr = ((df_daily["High"] - df_daily["Low"]) / df_daily["Close"] * 100).tail(20).mean()
        if recent_adr <= 4.0:
            return False

        # -----------------------------------------------------
        # Crossover & Candle Logic
        # -----------------------------------------------------
        sma50 = ta.sma(df_daily["Close"], length=50)
        if sma50 is None:
            return False
            
        # Price crossing 50 days SMA EXACTLY today
        prev_close = df_daily["Close"].iloc[-2]
        prev_sma50 = sma50.iloc[-2]
        curr_sma50 = sma50.iloc[-1]
        
        crossed_up = (prev_close <= prev_sma50) and (current_close > curr_sma50)
        
        if not crossed_up:
            return False

        # Solid bullish candle (body is a significant portion of the total range and close > open)
        if current_close <= current_open:
            return False
            
        total_range = current_high - current_low
        body_range = current_close - current_open
        
        if total_range == 0:
            return False
            
        if (body_range / total_range) < 0.50:
            return False

        # -----------------------------------------------------
        # RSI Checks
        # -----------------------------------------------------
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        
        if rsi_d is None or rsi_w is None:
            return False
            
        if rsi_d.iloc[-1] <= 40 or rsi_w.iloc[-1] <= 40:
            return False

        # -----------------------------------------------------
        # Bollinger Bands (Daily & Weekly)
        # -----------------------------------------------------
        bb_d = ta.bbands(df_daily["Close"], length=20, std=2)
        bb_w = ta.bbands(df_weekly["Close"], length=20, std=2)
        
        if bb_d is None or bb_w is None:
            return False
            
        # Extract via index to immune from column string name changes between TA versions
        bbl_d = bb_d.iloc[:, 0]
        bbu_d = bb_d.iloc[:, 2]
        
        # Daily: Lower band > Lower band prev day (rounding) OR Lower == Lower (flat) OR Upper > Upper prev day (rising)
        d_lower_rising_or_flat = bbl_d.iloc[-1] >= bbl_d.iloc[-2]
        d_upper_rising = bbu_d.iloc[-1] > bbu_d.iloc[-2]
        if not (d_lower_rising_or_flat or d_upper_rising):
            return False

        bbl_w = bb_w.iloc[:, 0]
        bbu_w = bb_w.iloc[:, 2]
        
        # Weekly: Lower bollinger is not declining WHEN upper bollinger band is flat or declining
        w_upper_flat_or_declining = bbu_w.iloc[-1] <= bbu_w.iloc[-2]
        w_lower_declining = bbl_w.iloc[-1] < bbl_w.iloc[-2]
        
        if w_upper_flat_or_declining and w_lower_declining:
            return False

        return True

    except Exception:
        return False
