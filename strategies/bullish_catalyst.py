import pandas as pd
from registry import register_screener
from asta_conditions import is_bbdnc, is_rsi_above, is_macd_up, is_solid_candle

@register_screener("Bullish_Catalyst")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    """
    Finviz-style Catalyst / Explosive Breakout Scanner:
    - Price > $1
    - Gain >= 10% from previous close
    - Volume >= 1,000,000
    - Relative Volume (vs 20-day avg) >= 3.0
    - Bullish conviction: Close >= Open, Close in upper half of today's range
    """
    try:
        df_daily = df_daily.dropna(subset=['Close', 'Volume'])
        if len(df_daily) < 22:
            return False

        current_close = df_daily['Close'].iloc[-1]
        current_open = df_daily['Open'].iloc[-1]
        current_volume = df_daily['Volume'].iloc[-1]
        prev_close = df_daily['Close'].iloc[-2]
        avg_volume_20 = df_daily['Volume'].rolling(window=20).mean().iloc[-2]

        # 1. Price > $1
        if pd.isna(current_close) or current_close <= 1.0:
            return False

        # 2. Change Up >= 10%
        pct_change = (current_close - prev_close) / prev_close
        if pd.isna(pct_change) or pct_change < 0.10:
            return False

        # 3. Volume >= 1M
        if pd.isna(current_volume) or current_volume < 1_000_000:
            return False

        # 4. Relative Volume >= 3x (vs prior 20 sessions)
        if pd.isna(avg_volume_20) or avg_volume_20 <= 0 or current_volume < (avg_volume_20 * 3.0):
            return False

        # 5. Bullish Structure (No gap-and-crap: Close >= Open)
        if current_close < current_open:
            return False

        # 6. Upper-half close (no massive rejection wick)
        daily_high = df_daily['High'].iloc[-1]
        daily_low = df_daily['Low'].iloc[-1]
        daily_range = daily_high - daily_low
        if daily_range > 0 and ((current_close - daily_low) / daily_range < 0.50):
            return False

        return True
    except Exception:
        return False
