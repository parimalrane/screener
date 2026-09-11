import pandas as pd
from registry import register_4h_screener
from asta_conditions import is_macd_pco, is_price_above_sma, is_rsi_above

@register_4h_screener("BU_4OS")
def check(df_4h: pd.DataFrame, df_weekly: pd.DataFrame):
    try:
        if len(df_weekly) < 30 or len(df_4h) < 20:
            return False

        if not is_price_above_sma(df_weekly, 20): return False
        if not is_macd_pco(df_weekly): return False
        if not is_rsi_above(df_weekly, 40): return False

        import pandas_ta as ta
        stoch_d = ta.stoch(df_4h["High"], df_4h["Low"], df_4h["Close"], k=14, d=3, smooth_k=3)
        if stoch_d is None or len(stoch_d) < 3: return False
            
        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]
        
        extreme = (k.iloc[-2] < 20) or (k.iloc[-3] < 20)
        if not extreme: return False
        
        crossed = (k.iloc[-1] > d.iloc[-1]) and (k.iloc[-2] <= d.iloc[-2])
        if not crossed: return False

        return True
    except Exception:
        return False
