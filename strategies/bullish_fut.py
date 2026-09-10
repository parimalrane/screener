import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_pco, is_macd_nco, is_price_above_sma, is_rsi_above, is_stoch_oversold_waiting
)

@register_screener("Bullish_FUT")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MONTHLY CONDITIONS (Macro Trend)
        # -----------------------------------------------------------------
        if not is_macd_pco(df_monthly): return False
        if not is_rsi_above(df_monthly, 60): return False
        if not is_price_above_sma(df_monthly, 20): return False
        
        # -----------------------------------------------------------------
        # WEEKLY CONDITIONS (The Pullback)
        # -----------------------------------------------------------------
        if not is_macd_nco(df_weekly): return False
        if not is_rsi_above(df_weekly, 40): return False
        
        # -----------------------------------------------------------------
        # DAILY CONDITIONS (Early Warning / Waiting to Trigger)
        # -----------------------------------------------------------------
        # We do NOT require MACD curling up yet.
        # We just want the Stochastic to be bleeding out in the oversold waiting zone.
        if not is_stoch_oversold_waiting(df_daily, threshold=30): return False

        return True

    except Exception:
        return False
