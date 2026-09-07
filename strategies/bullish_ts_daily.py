import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_rising, is_macd_nco, is_macd_pco, is_solid_candle, is_bkp, is_bbuc,
    is_ema_pco, is_rsi_above, is_price_above_sma, is_stoch_pco, is_stochastic_buy,
    is_volume_above_average
)

@register_screener("Bullish_TS_Daily")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MANDATORY CONDITIONS (Chartink Screenshot -> Medium Prob)
        # -----------------------------------------------------------------
        # Monthly Constraints
        if not is_macd_pco(df_monthly): return False
        if not is_rsi_above(df_monthly, 60): return False
        if not is_price_above_sma(df_monthly, 20): return False
        
        # Weekly Constraints
        if not is_macd_nco(df_weekly): return False
        if not is_rsi_above(df_weekly, 40): return False
        
        # Daily Constraints
        if not is_macd_rising(df_daily): return False
        if not is_stochastic_buy(df_daily, strict_crossover=True): return False

        # -----------------------------------------------------------------
        # HIGH PROBABILITY EVALUATION
        # -----------------------------------------------------------------
        # Since all "Better" conditions were removed, any setup passing the
        # brutal 7-rule mandatory gauntlet is automatically considered High Probability.
        return (True, "High")

    except Exception:
        return False