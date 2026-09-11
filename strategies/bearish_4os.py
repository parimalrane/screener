import pandas as pd
from registry import register_4h_screener
from asta_conditions import is_macd_nco, is_price_below_sma, is_rsi_below

@register_4h_screener("BE_4OS")
def check(df_4h: pd.DataFrame, df_weekly: pd.DataFrame):
    try:
        if len(df_weekly) < 30 or len(df_4h) < 20:
            return False

        if not is_price_below_sma(df_weekly, 20): return False
        if not is_macd_nco(df_weekly): return False
        if not is_rsi_below(df_weekly, 60): return False

        import pandas_ta as ta
        stoch_d = ta.stoch(df_4h["High"], df_4h["Low"], df_4h["Close"], k=14, d=3, smooth_k=3)
        if stoch_d is None or len(stoch_d) < 3: return False
            
        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]
        
        extreme = (k.iloc[-2] > 80) or (k.iloc[-3] > 80)
        if not extreme: return False
        
        crossed = (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
        if not crossed: return False

        return True
    except Exception:
        return False
