import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbdc,
    is_bbunc,
    is_macd_down,
    is_macd_nco,
    is_macd_declining,
    is_macd_below_zero,
    is_macd_down,
    is_rsi_below,
    is_price_below_sma,
    is_price_below_ema,
    is_ema_nco,
    is_adx_rising_or_above,
    is_di_bearish,    
    is_volume_above_average
)

# Helper functions centrally imported from asta_conditions

@register_screener("Bearish_MOM")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False
            
        # -----------------------------------------------------
        # MUST-HAVE: SUPER TIDE CONDITIONS (Monthly)
        # -----------------------------------------------------
        if not is_macd_down(df_monthly): return False

        # -----------------------------------------------------
        # MUST-HAVE: WEEKLY CONDITIONS (Tide)
        # -----------------------------------------------------
        # Tide - TI Downtick
        if not is_macd_declining(df_weekly): return False
        # Tide - BBDC OR Price in Lower Half
        if not (is_bbdc(df_weekly) or is_price_below_sma(df_weekly, 20)): return False
        # Tide & Wave - RSI < 50
        if not is_rsi_below(df_weekly, 50): return False

        # -----------------------------------------------------
        # MUST-HAVE: DAILY CONDITIONS (Wave)
        # -----------------------------------------------------
        # Tide & Wave - RSI < 50
        if not is_rsi_below(df_daily, 50): return False
        # Wave - BBDC
        if not is_bbdc(df_daily): return False
        # Wave - Above average Volume
        if not is_volume_above_average(df_daily, 20): return False
        # Wave - 5 EMA Negative Crossover
        if not (is_ema_nco(df_daily, 5, 13) or is_ema_nco(df_daily, 5, 26)): return False
        # Wave - ADX Ungali OR Above 15/20
        if not is_adx_rising_or_above(df_daily): return False
        
        # -----------------------------------------------------
        # HIGH/MEDIUM PROBABILITY EVALUATION (The "Betters")
        # -----------------------------------------------------
        tide_better = is_macd_below_zero(df_weekly)
        wave_rsi_better = is_rsi_below(df_daily, 40)
        wave_ema_better = is_price_below_ema(df_daily, 50)
        
        if tide_better and wave_rsi_better and wave_ema_better:
            return (True, "High")
        else:
            return (True, "Medium")

    except Exception:
        return False
