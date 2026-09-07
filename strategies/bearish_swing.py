import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbunc, is_solid_candle, is_bkt, is_volume_above_average,
    is_macd_declining, is_rsi_below, is_stoch_nco, is_di_bearish,
    is_stochastic_sell
)

@register_screener("Bearish_Swing")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------
        # MUST-HAVE: WEEKLY CONDITIONS (Tide)
        # -----------------------------------------------------
        # Tide - BBNC on Upside
        if not is_bbunc(df_weekly): return False

        # -----------------------------------------------------
        # MUST-HAVE: DAILY CONDITIONS (Wave)
        # -----------------------------------------------------
        # Chart Pattern: Bearish Reversal
        if not is_solid_candle(df_daily, 'bearish'): return False
        # Upper BB - BKT
        if not is_bkt(df_daily): return False
        # High Volume on Confirmation
        if not is_volume_above_average(df_daily, 20): return False
        # TI Downtick
        if not is_macd_declining(df_daily): return False
        # RSI < 60
        if not is_rsi_below(df_daily, 60): return False
        # Stochastic NCO
        if not is_stoch_nco(df_daily): return False
        # DI NCO
        if not is_di_bearish(df_daily): return False

        # -----------------------------------------------------
        # HIGH/MEDIUM PROBABILITY EVALUATION (The "Betters")
        # -----------------------------------------------------
        # The primary non-visual "Better" condition is Stochastic from Overbought
        stoch_overbought_better = is_stochastic_sell(df_daily, strict_crossover=False)
        
        if stoch_overbought_better:
            return (True, "High")
        else:
            return (True, "Medium")

    except Exception:
        return False
