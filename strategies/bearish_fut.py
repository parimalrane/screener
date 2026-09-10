import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_nco, is_macd_pco, is_price_below_sma, is_rsi_below, is_stoch_overbought_waiting
)

@register_screener("Bearish_FUT")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MONTHLY CONDITIONS (Macro Downtrend)
        # -----------------------------------------------------------------
        if not is_macd_nco(df_monthly): return False
        if not is_rsi_below(df_monthly, 40): return False
        if not is_price_below_sma(df_monthly, 20): return False
        
        # -----------------------------------------------------------------
        # WEEKLY CONDITIONS (The Bear Market Rally)
        # -----------------------------------------------------------------
        if not is_macd_pco(df_weekly): return False
        if not is_rsi_below(df_weekly, 60): return False
        
        # -----------------------------------------------------------------
        # DAILY CONDITIONS (Early Warning / Waiting to Drop)
        # -----------------------------------------------------------------
        # Stochastic is pushed high into the overbought ceiling waiting to cross down.
        if not is_stoch_overbought_waiting(df_daily, threshold=70): return False

        return True

    except Exception:
        return False
