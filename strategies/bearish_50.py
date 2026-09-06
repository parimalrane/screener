import pandas as pd
import pandas_ta as ta
from registry import register_screener

@register_screener("Bearish_50")
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
            # If Lower BB is declining, price MUST strictly sit below the 20 SMA
            if df_weekly["Close"].iloc[-1] >= sma_w.iloc[-1]:
                return False
        else:
            # If Lower BB is flat or rising, the Upper BB is explicitly forbidden from rising (no bullish expansion)
            w_upper_rising = bbu_w.iloc[-1] > bbu_w.iloc[-2]
            if w_upper_rising:
                return False
            
        # 2. Weekly MACD line < Weekly Signal Line
        macd_line_w = macd_w["MACD_12_26_9"].iloc[-1]
        macd_signal_w = macd_w["MACDs_12_26_9"].iloc[-1]
        if macd_line_w >= macd_signal_w:
            return False
            
        # 3. Weekly RSI < 50
        if rsi_w.iloc[-1] >= 50:
            return False

        # -----------------------------------------------------
        # DAILY CONDITIONS (BEARISH WAVE)
        # -----------------------------------------------------
        bb_d = ta.bbands(df_daily["Close"], length=20, std=2)
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        sma50_d = ta.sma(df_daily["Close"], length=50)
        sma20_d = ta.sma(df_daily["Close"], length=20)
        
        if bb_d is None or rsi_d is None or sma50_d is None or sma20_d is None:
            return False
            
        bbl_d = bb_d.iloc[:, 0]  # Lower band
        
        # 4. Daily BBLC: Lower band actively dropping AND Price < 20 SMA
        if bbl_d.iloc[-1] >= bbl_d.iloc[-2]:
            return False
        if current_close >= sma20_d.iloc[-1]:
            return False
            
        # 5. Daily RSI < 45
        if rsi_d.iloc[-1] >= 45:
            return False
            
        # 5.5 Daily ADX Logic (-DI > +DI and ADX is rising)
        adx_d = ta.adx(df_daily["High"], df_daily["Low"], df_daily["Close"], length=14)
        if adx_d is None:
            return False
            
        adx_col = [c for c in adx_d.columns if c.startswith("ADX")][0]
        dmp_col = [c for c in adx_d.columns if c.startswith("DMP")][0]
        dmn_col = [c for c in adx_d.columns if c.startswith("DMN")][0]
        
        # -DI > +DI  (Minus Directional Indicator signifies downward strength)
        if adx_d[dmn_col].iloc[-1] <= adx_d[dmp_col].iloc[-1]:
            return False
            
        # ADX is rising OR ADX > 15 (ADX values are non-directional trend strength, so this rule is identical to Bullish)
        adx_rising = adx_d[adx_col].iloc[-1] > adx_d[adx_col].iloc[-2]
        adx_above_15 = adx_d[adx_col].iloc[-1] > 15
        
        if not (adx_rising or adx_above_15):
            return False
            
        # 6. The 50 SMA Trap (Bearish Breakdown OR 5% Proximity)
        prev_close = df_daily["Close"].iloc[-2]
        prev_sma50 = sma50_d.iloc[-2]
        curr_sma50 = sma50_d.iloc[-1]
        
        # Scenario A: Exact Downward Breakdown
        exact_cross_down = (prev_close >= prev_sma50) and (current_close < curr_sma50)
        
        # Scenario B: 2% Proximity Zone (Must be strictly BELOW 50 SMA, but not strictly more than 2% away)
        is_below = current_close < curr_sma50
        pct_diff = (curr_sma50 - current_close) / curr_sma50
        within_2_pct = is_below and (pct_diff <= 0.02)
        
        if not (exact_cross_down or within_2_pct):
            return False

        return True

    except Exception:
        return False
