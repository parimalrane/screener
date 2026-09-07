import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbuc,
    is_bbdnc,
    is_macd_up,
    is_macd_pco,
    is_macd_rising,
    is_macd_above_zero,
    is_rsi_above,
    is_price_above_sma,
    is_price_above_ema,
    is_ema_pco,
    is_adx_rising_or_above,
    is_di_bullish,
    is_volume_above_average
)

@register_screener("Bullish_MOM")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------
        # MUST-HAVE: WEEKLY CONDITIONS (Tide)
        # -----------------------------------------------------
        # Tide - TI Uptick
        if not is_macd_rising(df_weekly): return False
        # Tide - BBUC OR Price in Upper Half
        if not (is_bbuc(df_weekly) or is_price_above_sma(df_weekly, 20)): return False
        # Tide & Wave - RSI > 50
        if not is_rsi_above(df_weekly, 50): return False

        # -----------------------------------------------------
        # MUST-HAVE: DAILY CONDITIONS (Wave)
        # -----------------------------------------------------
        # Tide & Wave - RSI > 50
        if not is_rsi_above(df_daily, 50): return False
        # Wave - BBUC
        if not is_bbuc(df_daily): return False
        # Wave - Above average Volume
        if not is_volume_above_average(df_daily, 20): return False
        # Wave - 5 EMA Positive Crossover
        if not (is_ema_pco(df_daily, 5, 13) or is_ema_pco(df_daily, 5, 26)): return False
        # Wave - DI PCO
        if not is_di_bullish(df_daily): return False
        # Wave - ADX Ungli OR Above 15
        if not is_adx_rising_or_above(df_daily): return False
        
        # -----------------------------------------------------
        # HIGH/MEDIUM PROBABILITY EVALUATION (The "Betters")
        # -----------------------------------------------------
        tide_better = is_macd_above_zero(df_weekly)
        wave_rsi_better = is_rsi_above(df_daily, 60)
        wave_ema_better = is_price_above_ema(df_daily, 50)
        
        if tide_better and wave_rsi_better and wave_ema_better:
            return (True, "High")
        else:
            return (True, "Medium")

    except Exception:
        return False
