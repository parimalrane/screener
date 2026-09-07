import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbdnc, is_solid_candle, is_bkp, is_volume_above_average,
    is_macd_rising, is_rsi_above, is_stoch_pco, is_di_bullish,
    is_stochastic_buy
)

@register_screener("Bullish_Swing")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------
        # MUST-HAVE: WEEKLY CONDITIONS (Tide)
        # -----------------------------------------------------
        # Tide - BBNC on Downside
        if not is_bbdnc(df_weekly): return False

        # -----------------------------------------------------
        # MUST-HAVE: DAILY CONDITIONS (Wave)
        # -----------------------------------------------------
        # Candle Pattern: Bullish Reversal
        if not is_solid_candle(df_daily, 'bullish'): return False
        # Lower BB - BKP
        if not is_bkp(df_daily): return False
        # High Volume on Confirmation
        if not is_volume_above_average(df_daily, 20): return False
        # TI Uptick
        if not is_macd_rising(df_daily): return False
        # RSI > 40
        if not is_rsi_above(df_daily, 40): return False
        # Stochastic PCO
        if not is_stoch_pco(df_daily): return False
        # DI PCO
        if not is_di_bullish(df_daily): return False

        # -----------------------------------------------------
        # HIGH/MEDIUM PROBABILITY EVALUATION (The "Betters")
        # -----------------------------------------------------
        # The primary non-visual "Better" condition is Stochastic from Oversold
        stoch_oversold_better = is_stochastic_buy(df_daily, strict_crossover=False)
        
        if stoch_oversold_better:
            return (True, "High")
        else:
            return (True, "Medium")

    except Exception:
        return False
