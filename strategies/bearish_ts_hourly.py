import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_declining, is_macd_pco, is_macd_nco, is_solid_candle, is_bkt, is_bbdc,
    is_ema_nco, is_rsi_below, is_price_below_sma, is_stoch_nco, is_stochastic_sell,
    is_volume_above_average, is_macd_down
)

@register_screener("Bearish_TS_Hourly")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    """
    Evaluates only the Tide (Weekly) and Wave (Daily) structures.
    The final Ripple (Hourly) execution is intentionally skipped for manual chart verification.
    """
    try:
        if len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # -----------------------------------------------------------------
        # MANDATORY CONDITIONS
        # -----------------------------------------------------------------
        # Super Tide Contingency (Monthly) - Ignores IPOs lacking 30-month history
        if len(df_monthly) >= 30:
            if not is_macd_down(df_monthly): return False
            
        # Tide Constraints (Weekly)
        if not is_macd_nco(df_weekly): return False
        if not is_rsi_below(df_weekly, 40): return False
        if not is_price_below_sma(df_weekly, 20): return False
        
        # Wave Constraints (Daily)
        if not is_macd_pco(df_daily): return False
        if not is_rsi_below(df_daily, 60): return False
        
        # Ripple Constraints (Hourly) - SKIPPED FOR MANUAL VERIFICATION

        # -----------------------------------------------------------------
        # HIGH PROBABILITY EVALUATION
        # -----------------------------------------------------------------
        return (True, "High")

    except Exception:
        return False
