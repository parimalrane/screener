import pandas as pd
import pandas_ta as ta
from registry import register_screener

@register_screener("Bearish_MOM")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    try:
        if len(df_daily) < 55 or len(df_weekly) < 25:
            return False

        current_close = df_daily["Close"].iloc[-1]

        # -----------------------------------------------------
        # WEEKLY CONDITIONS (BEARISH TIDE)
        # -----------------------------------------------------
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        sma_w = ta.sma(df_weekly["Close"], length=20)
        
        if macd_w is None or rsi_w is None or sma_w is None:
            return False
            
        # 1. Weekly Bollinger Band Structural Branching
        bb_w = ta.bbands(df_weekly["Close"], length=20, std=2)
        if bb_w is None:
            return False
            
        bbu_w = bb_w.iloc[:, 2]
        bbl_w = bb_w.iloc[:, 0]
        
        w_lower_declining = bbl_w.iloc[-1] < bbl_w.iloc[-2]
        
        if w_lower_declining:
            if df_weekly["Close"].iloc[-1] >= sma_w.iloc[-1]: return False
        else:
            w_upper_rising = bbu_w.iloc[-1] > bbu_w.iloc[-2]
            if w_upper_rising: return False
            
        # 2. Weekly MACD line < Weekly Signal Line
        macd_line_w = macd_w["MACD_12_26_9"].iloc[-1]
        macd_signal_w = macd_w["MACDs_12_26_9"].iloc[-1]
        if macd_line_w >= macd_signal_w: return False
            
        # 3. Weekly RSI < 50
        if rsi_w.iloc[-1] >= 50: return False

        # -----------------------------------------------------
        # DAILY CONDITIONS (BEARISH WAVE)
        # -----------------------------------------------------
        bb_d = ta.bbands(df_daily["Close"], length=20, std=2)
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        sma50_d = ta.sma(df_daily["Close"], length=50)
        sma20_d = ta.sma(df_daily["Close"], length=20)
        
        if bb_d is None or rsi_d is None or sma50_d is None or sma20_d is None: return False
            
        bbl_d = bb_d.iloc[:, 0]
        
        # 4. Daily BBLC: Lower band actively dropping AND Price < 20 SMA
        if bbl_d.iloc[-1] >= bbl_d.iloc[-2]: return False
        if current_close >= sma20_d.iloc[-1]: return False
            
        # 5. Daily RSI < 45
        if rsi_d.iloc[-1] >= 45: return False
            
        # 5.5 Daily ADX Logic (-DI > +DI and ADX is rising OR ADX > 15)
        adx_d = ta.adx(df_daily["High"], df_daily["Low"], df_daily["Close"], length=14)
        if adx_d is None: return False
            
        adx_col = [c for c in adx_d.columns if c.startswith("ADX")][0]
        dmp_col = [c for c in adx_d.columns if c.startswith("DMP")][0]
        dmn_col = [c for c in adx_d.columns if c.startswith("DMN")][0]
        
        if adx_d[dmn_col].iloc[-1] <= adx_d[dmp_col].iloc[-1]: return False
            
        adx_rising = adx_d[adx_col].iloc[-1] > adx_d[adx_col].iloc[-2]
        adx_above_15 = adx_d[adx_col].iloc[-1] > 15
        if not (adx_rising or adx_above_15): return False
            
        # 6. EXACT SMA BREAKDOWN WITH VOLUME SURGE
        if df_daily["Volume"].iloc[-1] <= df_daily["Volume"].tail(20).mean(): return False
            
        prev_close = df_daily["Close"].iloc[-2]
        
        prev_sma50 = sma50_d.iloc[-2]
        curr_sma50 = sma50_d.iloc[-1]
        exact_cross_50 = (prev_close >= prev_sma50) and (current_close < curr_sma50)
        
        prev_sma20 = sma20_d.iloc[-2]
        curr_sma20 = sma20_d.iloc[-1]
        exact_cross_20 = (prev_close >= prev_sma20) and (current_close < curr_sma20)
        
        if not (exact_cross_50 or exact_cross_20):
            return False

        return True

    except Exception:
        return False
