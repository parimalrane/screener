import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_down, is_rsi_below, is_price_below_sma,
    is_macd_up, is_bbunc,
    is_macd_declining, is_stochastic_sell
)

@register_screener("Bearish_Daily_2")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MANDATORY CONDITIONS
        # -----------------------------------------------------------------
        # Monthly Constraints
        if not is_macd_down(df_monthly): return False
        if not is_rsi_below(df_monthly, 50): return False
        if not is_price_below_sma(df_monthly, 20): return False
        
        # Weekly Constraints
        if not is_macd_up(df_weekly): return False
        if not is_rsi_below(df_weekly, 60): return False
        if not is_bbunc(df_weekly): return False
        
        # Daily Constraints
        if not is_macd_declining(df_daily): return False
        if not is_stochastic_sell(df_daily, strict_crossover=True): return False

        return (True, "High")

    except Exception:
        return False
