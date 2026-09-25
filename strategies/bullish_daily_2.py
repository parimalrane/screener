import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_up, is_rsi_above, is_price_above_sma,
    is_macd_down, is_bbdnc,
    is_macd_rising, is_stochastic_buy
)

@register_screener("Bullish_Daily_2")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MANDATORY CONDITIONS
        # -----------------------------------------------------------------
        # Monthly Constraints
        if not is_macd_up(df_monthly): return False
        if not is_rsi_above(df_monthly, 50): return False
        if not is_price_above_sma(df_monthly, 20): return False
        
        # Weekly Constraints
        if not is_macd_down(df_weekly): return False
        if not is_rsi_above(df_weekly, 40): return False
        if not is_bbdnc(df_weekly): return False
        
        # Daily Constraints
        if not is_macd_rising(df_daily): return False
        if not is_stochastic_buy(df_daily, strict_crossover=True): return False

        return (True, "High")

    except Exception:
        return False
