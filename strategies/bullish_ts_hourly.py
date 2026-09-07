import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_macd_rising, is_macd_nco, is_macd_pco, is_solid_candle, is_bkp, is_bbuc,
    is_ema_pco, is_rsi_above, is_price_above_sma, is_stoch_pco, is_stochastic_buy,
    is_volume_above_average, is_macd_up
)

@register_screener("Bullish_TS_Hourly")
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
            if not is_macd_up(df_monthly): return False
            
        # Tide Constraints (Weekly)
        if not is_macd_pco(df_weekly): return False
        if not is_rsi_above(df_weekly, 60): return False
        if not is_price_above_sma(df_weekly, 20): return False
        
        # Wave Constraints (Daily)
        if not is_macd_nco(df_daily): return False
        if not is_rsi_above(df_daily, 40): return False
        
        # Ripple Constraints (Hourly) - SKIPPED FOR MANUAL VERIFICATION

        # -----------------------------------------------------------------
        # HIGH PROBABILITY EVALUATION
        # -----------------------------------------------------------------
        return (True, "High")

    except Exception:
        return False
