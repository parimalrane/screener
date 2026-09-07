import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_declining, is_macd_pco, is_macd_nco, is_solid_candle, is_bkt, is_bbdc,
    is_ema_nco, is_rsi_below, is_price_below_sma, is_stoch_nco, is_stochastic_sell,
    is_volume_above_average
)

@register_screener("Bearish_TS_Daily")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MANDATORY CONDITIONS (Chartink Screenshot -> Medium Prob)
        # -----------------------------------------------------------------
        # Monthly Constraints
        if not is_macd_nco(df_monthly): return False
        if not is_rsi_below(df_monthly, 40): return False
        if not is_price_below_sma(df_monthly, 20): return False
        
        # Weekly Constraints
        if not is_macd_pco(df_weekly): return False
        if not is_rsi_below(df_weekly, 60): return False
        
        # Daily Constraints
        if not is_macd_declining(df_daily): return False
        if not is_stochastic_sell(df_daily, strict_crossover=True): return False

        # -----------------------------------------------------------------
        # HIGH PROBABILITY EVALUATION
        # -----------------------------------------------------------------
        # Since all "Better" conditions were removed, any setup passing the
        # brutal 7-rule mandatory gauntlet is automatically considered High Probability.
        return (True, "High")

    except Exception:
        return False
