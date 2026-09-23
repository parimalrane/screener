import pandas as pd
from registry import register_screener
from asta_conditions import (
    is_bbunc, is_macd_nco, is_rsi_below,
    is_macd_up, is_macd_bearish_hook, is_bkt
)

@register_screener("Bearish_Hook")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    """
    MACD Bearish Hook Scanner — Failed PCO continuation setup.

    Monthly:
    - Upside BB not challenged
    - MACD NCO
    - RSI < 60

    Weekly:
    - MACD Up (bounce phase)
    - Upside BB not challenged

    Daily:
    - MACD Bearish Hook (failed PCO, hooked back down)
    - RSI < 60
    - BKT (Upper BB ceiling / rounding top)
    """
    try:
        if len(df_monthly) < 50 or len(df_weekly) < 50 or len(df_daily) < 50:
            return False

        # Monthly Conditions (Macro Trend)
        if not is_bbunc(df_monthly): return False
        if not is_macd_nco(df_monthly): return False
        if not is_rsi_below(df_monthly, 60): return False

        # Weekly Conditions (Bounce)
        if not is_macd_up(df_weekly): return False
        if not is_bbunc(df_weekly): return False

        # Daily Conditions (The Hook)
        if not is_macd_bearish_hook(df_daily): return False
        if not is_rsi_below(df_daily, 60): return False
        if not is_bkt(df_daily): return False

        return True

    except Exception:
        return False
