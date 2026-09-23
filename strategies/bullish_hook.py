import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbdnc, is_macd_pco, is_rsi_above,
    is_macd_down, is_macd_bullish_hook, is_bkp
)

@register_screener("Bullish_Hook")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    """
    MACD Bullish Hook Scanner — Failed NCO continuation setup.

    Monthly:
    - Downside BB not challenged
    - MACD PCO
    - RSI > 40

    Weekly:
    - MACD Down (pullback phase)
    - Downside BB not challenged

    Daily:
    - MACD Bullish Hook (failed NCO, hooked back up)
    - RSI > 40
    - BKP (Lower BB floor / rounding bottom)
    """
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # Monthly Conditions (Macro Trend)
        if not is_bbdnc(df_monthly): return False
        if not is_macd_pco(df_monthly): return False
        if not is_rsi_above(df_monthly, 40): return False

        # Weekly Conditions (Pullback)
        if not is_macd_down(df_weekly): return False
        if not is_bbdnc(df_weekly): return False

        # Daily Conditions (The Hook)
        if not is_macd_bullish_hook(df_daily): return False
        if not is_rsi_above(df_daily, 40): return False
        if not is_bkp(df_daily): return False

        return True

    except Exception:
        return False
