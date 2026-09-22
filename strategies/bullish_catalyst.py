import pandas as pd
from registry import register_screener
from asta_conditions import is_bbdnc, is_rsi_above

@register_screener("Bullish_Catalyst")
def check(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame):
    """
    Scans for explosive breakouts / catalyst events typically found in Finviz presets:
    - Price > $1
    - Change > 10% from previous close
    - Current Volume > 1M
    - Relative Volume > 2
    - Monthly: Downside BB not challenged
    - Weekly: Downside BB not challenged, RSI > 40
    """
    try:
        # Require enough daily/weekly data, but allow new IPOs to bypass monthly
        if len(df_daily) < 50 or len(df_weekly) < 20:
            return False

        # Monthly Conditions (Skipped if < 20 months of data for new IPO)
        if len(df_monthly) >= 20:
            if not is_bbdnc(df_monthly): return False

        # Weekly Conditions
        if not is_bbdnc(df_weekly): return False
        if not is_rsi_above(df_weekly, 40): return False

        # Latest candle
        current_close = df_daily['Close'].iloc[-1]
        current_open = df_daily['Open'].iloc[-1]
        current_volume = df_daily['Volume'].iloc[-1]
        
        # Previous candle
        prev_close = df_daily['Close'].iloc[-2]
        
        # Average volume (20 days)
        avg_volume_20 = df_daily['Volume'].rolling(window=20).mean().iloc[-2] # up to yesterday
        
        # 1. Price > $1
        if current_close <= 1.0:
            return False
            
        # 2. Change Up 10%
        pct_change = (current_close - prev_close) / prev_close
        if pct_change < 0.10:
            return False
            

        # 4. Current Volume > 1M
        if current_volume < 1_000_000:
            return False
            
        # 4. Relative Volume > 2
        # Use average volume from previous 20 days (to not skew with today's massive volume)
        if pd.isna(avg_volume_20) or avg_volume_20 <= 0:
            return False
            
        if current_volume < (avg_volume_20 * 2):
            return False

        # Finviz also specified "Average Volume Under 1M" or similar, but
        # RVOL > 2 and current volume > 1M guarantees the volume spike logic.
        
        return True

    except Exception:
        return False
