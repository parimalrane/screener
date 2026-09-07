import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_pco, is_macd_nco, is_macd_declining,
    is_rsi_below, is_price_below_sma, is_stochastic_sell,
    is_bkt, is_bbdc, is_solid_candle, is_ema_nco, is_volume_above_average
)

@register_screener("Bearish_TS_Daily")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # CHARTINK GOLDEN RULES (MANDATORY)
        # -----------------------------------------------------------------
        # Monthly Constraints (Inverted)
        if not is_macd_nco(df_monthly): return False
        if not is_rsi_below(df_monthly, 40): return False
        if not is_price_below_sma(df_monthly, 20): return False

        # Weekly Constraints (Inverted)
        if not is_macd_pco(df_weekly): return False
        if not is_rsi_below(df_weekly, 60): return False

        # Daily Constraints (Inverted)
        if not is_macd_declining(df_daily): return False
        if not is_stochastic_sell(df_daily, strict_crossover=True): return False

        # -----------------------------------------------------------------
        # DASHBOARD BONUS COLUMNS (From Official PDF)
        # -----------------------------------------------------------------
        tags = ""
        if is_bkt(df_daily) or is_bbdc(df_daily): tags += "*"
        
        return (True, tags)

    except Exception:
        return False
