import pandas as pd
import pandas_ta as ta

def _get_indicators(df: pd.DataFrame, length: int = 20, std: float = 2.0):
    """Helper method to extract the Bollinger Bands and 20 SMA."""
    bb = ta.bbands(df["Close"], length=length, std=std)
    sma = ta.sma(df["Close"], length=length)
    
    if bb is None or sma is None or len(df) < length:
        return None, None
        
    bbl = bb.iloc[:, 0]  # Lower band
    bbu = bb.iloc[:, 2]  # Upper band
    return {'bbu': bbu, 'bbl': bbl}, sma

# ---------------------------------------------------------
# ASTA TOOLBOX
# ---------------------------------------------------------

def is_bbuc(df: pd.DataFrame) -> bool:
    """1. Bollinger Band Upper Challenged"""
    bands, sma = _get_indicators(df)
    if not bands: return False
    
    curr_bbu = bands['bbu'].iloc[-1]
    prev_bbu = bands['bbu'].iloc[-2]
    curr_close = df["Close"].iloc[-1]
    curr_sma = sma.iloc[-1]
    
    upper_rising = curr_bbu > prev_bbu
    price_above_sma = curr_close > curr_sma
    
    return upper_rising and price_above_sma

def is_bbufc(df: pd.DataFrame, lookback: int = 4) -> bool:
    """2. Bollinger Band Upper Failed Challenge"""
    bands, _ = _get_indicators(df)
    if not bands or len(df) < lookback: return False
    
    # Condition 1: Attack (High >= Upper BB in last N candles)
    attack = False
    for i in range(-lookback, 0):
        if df["High"].iloc[i] >= bands['bbu'].iloc[i]:
            attack = True
            break
            
    # Condition 2: Rejection (Candle is bearish)
    curr_close = df["Close"].iloc[-1]
    curr_open = df["Open"].iloc[-1]
    bearish = curr_close < curr_open
    
    # Condition 3: Flatline
    curr_bbu = bands['bbu'].iloc[-1]
    prev_bbu = bands['bbu'].iloc[-2]
    upper_flat = curr_bbu <= prev_bbu
    
    return attack and bearish and upper_flat

def is_bbdc(df: pd.DataFrame) -> bool:
    """3. Bollinger Band Downside Challenged"""
    bands, sma = _get_indicators(df)
    if not bands: return False
    
    curr_bbl = bands['bbl'].iloc[-1]
    prev_bbl = bands['bbl'].iloc[-2]
    curr_close = df["Close"].iloc[-1]
    curr_sma = sma.iloc[-1]
    
    lower_declining = curr_bbl < prev_bbl
    price_below_sma = curr_close < curr_sma
    
    return lower_declining and price_below_sma

def is_bbunc(df: pd.DataFrame) -> bool:
    """4. Bollinger Band Upside Not Challenged"""
    bands, sma = _get_indicators(df)
    if not bands: return False
    
    curr_bbu = bands['bbu'].iloc[-1]
    prev_bbu = bands['bbu'].iloc[-2]
    curr_bbl = bands['bbl'].iloc[-1]
    prev_bbl = bands['bbl'].iloc[-2]
    curr_close = df["Close"].iloc[-1]
    curr_sma = sma.iloc[-1]
    
    upper_flat = curr_bbu <= prev_bbu
    artificial_expansion = (curr_bbu > prev_bbu) and (curr_close < curr_sma) and (curr_bbl < prev_bbl)
    
    return upper_flat or artificial_expansion

def is_bbdnc(df: pd.DataFrame) -> bool:
    """5. Bollinger Band Downside Not Challenged"""
    bands, sma = _get_indicators(df)
    if not bands: return False
    
    curr_bbl = bands['bbl'].iloc[-1]
    prev_bbl = bands['bbl'].iloc[-2]
    curr_bbu = bands['bbu'].iloc[-1]
    prev_bbu = bands['bbu'].iloc[-2]
    curr_close = df["Close"].iloc[-1]
    curr_sma = sma.iloc[-1]
    
    lower_flat = curr_bbl >= prev_bbl
    artificial_expansion = (curr_bbl < prev_bbl) and (curr_close > curr_sma) and (curr_bbu > prev_bbu)
    
    return lower_flat or artificial_expansion

def is_bkp(df: pd.DataFrame) -> bool:
    """6. Babaji Ka Prasad (Rounding Bottom / Flat Lower Board)"""
    bands, _ = _get_indicators(df)
    if not bands: return False
    
    curr_bbl = bands['bbl'].iloc[-1]
    prev_bbl = bands['bbl'].iloc[-2]
    
    return curr_bbl >= prev_bbl

def is_bkt(df: pd.DataFrame) -> bool:
    """7. Bapu Ka Tapli (Rounding Top / Flat Upper Board)"""
    bands, _ = _get_indicators(df)
    if not bands: return False
    
    curr_bbu = bands['bbu'].iloc[-1]
    prev_bbu = bands['bbu'].iloc[-2]
    
    return curr_bbu <= prev_bbu

def is_bbdfc(df: pd.DataFrame, lookback: int = 4) -> bool:
    """8. Bollinger Band Downside Failed Challenge"""
    bands, _ = _get_indicators(df)
    if not bands or len(df) < lookback: return False
    
    # Condition 1: Attack (Low <= Lower BB in last N candles)
    attack = False
    for i in range(-lookback, 0):
        if df["Low"].iloc[i] <= bands['bbl'].iloc[i]:
            attack = True
            break
            
    # Condition 2: Support (Flatline or Rising)
    curr_bbl = bands['bbl'].iloc[-1]
    prev_bbl = bands['bbl'].iloc[-2]
    lower_flat = curr_bbl >= prev_bbl
    
    return attack and lower_flat

def is_adx_ungali(df: pd.DataFrame, length: int = 14) -> bool:
    """9. ADX Ungali (ADX Finger)"""
    if len(df) < length * 2: return False
    
    adx_df = ta.adx(df["High"], df["Low"], df["Close"], length=length)
    if adx_df is None or len(adx_df) < 2: return False
    
    adx_col = [c for c in adx_df.columns if c.startswith("ADX")][0]
    curr_adx = adx_df[adx_col].iloc[-1]
    prev_adx = adx_df[adx_col].iloc[-2]
    
    # Rising above 15 OR already above 20
    return (curr_adx > 15 and curr_adx > prev_adx) or (curr_adx > 20)

def is_solid_candle(df: pd.DataFrame, direction: str = 'bullish') -> bool:
    """10. Solid Candle (Not Neutral or Tiny)"""
    if len(df) < 20: return False
    
    curr_high = df["High"].iloc[-1]
    curr_low = df["Low"].iloc[-1]
    curr_open = df["Open"].iloc[-1]
    curr_close = df["Close"].iloc[-1]
    
    # 1. Not Tiny: Range >= 50% of 20-day ADR
    range_series = df["High"] - df["Low"]
    adr_20 = range_series.rolling(window=20).mean().iloc[-1]
    curr_range = curr_high - curr_low
    
    if curr_range < (0.50 * adr_20):
        return False
        
    # 2. Not Neutral: Body >= 51% of Total Range
    if curr_range == 0: return False
    body = abs(curr_close - curr_open)
    if (body / curr_range) < 0.51:
        return False
        
    # 3. Direction Check
    if direction == 'bullish':
        return curr_close > curr_open
    elif direction == 'bearish':
        return curr_close < curr_open
        
    return False

def is_macd_rising(df: pd.DataFrame) -> bool:
    """Helper: MACD Line is rising"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 2: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    return macd_df[macd_col].iloc[-1] > macd_df[macd_col].iloc[-2]

def is_macd_declining(df: pd.DataFrame) -> bool:
    """Helper: MACD Line is declining"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 2: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    return macd_df[macd_col].iloc[-1] < macd_df[macd_col].iloc[-2]

def is_macd_pco(df: pd.DataFrame) -> bool:
    """Helper: MACD Positive Crossover (Line > Signal)"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 1: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    signal_col = [c for c in macd_df.columns if c.startswith("MACDs_")][0]
    return macd_df[macd_col].iloc[-1] > macd_df[signal_col].iloc[-1]

def is_macd_nco(df: pd.DataFrame) -> bool:
    """Helper: MACD Negative Crossover (Line < Signal)"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 1: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    signal_col = [c for c in macd_df.columns if c.startswith("MACDs_")][0]
    return macd_df[macd_col].iloc[-1] < macd_df[signal_col].iloc[-1]

def is_stoch_pco(df: pd.DataFrame) -> bool:
    """Helper: Stochastic flowing in Positive Crossover State"""
    if len(df) < 14: return False
    stoch_df = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_df is None or len(stoch_df) < 1: return False
    
    k_col = [c for c in stoch_df.columns if c.startswith("STOCHk")][0]
    d_col = [c for c in stoch_df.columns if c.startswith("STOCHd")][0]
    
    return stoch_df[k_col].iloc[-1] > stoch_df[d_col].iloc[-1]

def is_stoch_nco(df: pd.DataFrame) -> bool:
    """Helper: Stochastic flowing in Negative Crossover State"""
    if len(df) < 14: return False
    stoch_df = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_df is None or len(stoch_df) < 1: return False
    
    k_col = [c for c in stoch_df.columns if c.startswith("STOCHk")][0]
    d_col = [c for c in stoch_df.columns if c.startswith("STOCHd")][0]
    
    return stoch_df[k_col].iloc[-1] < stoch_df[d_col].iloc[-1]

def is_stochastic_buy(df: pd.DataFrame, strict_crossover: bool = True) -> bool:
    """Helper: Stochastic Oversold Buy Signal"""
    if len(df) < 14: return False
    stoch_df = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_df is None or len(stoch_df) < 3: return False
    
    k_col = [c for c in stoch_df.columns if c.startswith("STOCHk")][0]
    d_col = [c for c in stoch_df.columns if c.startswith("STOCHd")][0]
    
    k = stoch_df[k_col]
    d = stoch_df[d_col]
    
    oversold = k.iloc[-3] < 30
    if strict_crossover:
        trigger = (k.iloc[-1] > d.iloc[-1]) and (k.iloc[-2] <= d.iloc[-2])
    else:
        trigger = k.iloc[-1] > d.iloc[-1]
        
    return oversold and trigger

def is_stochastic_sell(df: pd.DataFrame, strict_crossover: bool = True) -> bool:
    """Helper: Stochastic Overbought Sell Signal"""
    if len(df) < 14: return False
    stoch_df = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_df is None or len(stoch_df) < 3: return False
    
    k_col = [c for c in stoch_df.columns if c.startswith("STOCHk")][0]
    d_col = [c for c in stoch_df.columns if c.startswith("STOCHd")][0]
    
    k = stoch_df[k_col]
    d = stoch_df[d_col]
    
    overbought = k.iloc[-3] > 70
    if strict_crossover:
        trigger = (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
    else:
        trigger = k.iloc[-1] < d.iloc[-1]
        
    return overbought and trigger

def is_rsi_above(df: pd.DataFrame, threshold: float = 50, length: int = 14) -> bool:
    """Helper: RSI strictly > threshold"""
    if len(df) < length: return False
    rsi_series = ta.rsi(df["Close"], length=length)
    if rsi_series is None or len(rsi_series) < 1: return False
    return rsi_series.iloc[-1] > threshold

def is_rsi_below(df: pd.DataFrame, threshold: float = 50, length: int = 14) -> bool:
    """Helper: RSI strictly < threshold"""
    if len(df) < length: return False
    rsi_series = ta.rsi(df["Close"], length=length)
    if rsi_series is None or len(rsi_series) < 1: return False
    return rsi_series.iloc[-1] < threshold

def is_macd_above_zero(df: pd.DataFrame) -> bool:
    """Helper: MACD Line > 0"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 1: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    return macd_df[macd_col].iloc[-1] > 0

def is_macd_below_zero(df: pd.DataFrame) -> bool:
    """Helper: MACD Line < 0"""
    if len(df) < 30: return False
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 1: return False
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_")][0]
    return macd_df[macd_col].iloc[-1] < 0

def is_price_above_ema(df: pd.DataFrame, length: int = 50) -> bool:
    """Helper: Close Price > EMA"""
    if len(df) < length: return False
    ema_s = ta.ema(df["Close"], length=length)
    if ema_s is None or len(ema_s) < 1: return False
    return df["Close"].iloc[-1] > ema_s.iloc[-1]

def is_ema_pco(df: pd.DataFrame, short_len: int = 5, long_len: int = 13) -> bool:
    """Helper: Short EMA > Long EMA (Positive Crossover State)"""
    if len(df) < long_len: return False
    ema_s = ta.ema(df["Close"], length=short_len)
    ema_l = ta.ema(df["Close"], length=long_len)
    if ema_s is None or ema_l is None: return False
    return ema_s.iloc[-1] > ema_l.iloc[-1]

def is_adx_rising_or_above(df: pd.DataFrame, length: int = 14) -> bool:
    """Helper: Custom ADX momentum logic (Rising > 12 OR already > 20)"""
    if len(df) < length * 2: return False
    adx_df = ta.adx(df["High"], df["Low"], df["Close"], length=length)
    if adx_df is None or len(adx_df) < 2: return False
    adx_col = [c for c in adx_df.columns if c.startswith("ADX")][0]
    curr_adx = adx_df[adx_col].iloc[-1]
    prev_adx = adx_df[adx_col].iloc[-2]
    
    if (curr_adx > prev_adx) and (curr_adx > 12): return True
    if curr_adx > 20: return True
    return False

def is_di_bullish(df: pd.DataFrame, length: int = 14) -> bool:
    """Helper: +DI > -DI"""
    if len(df) < length * 2: return False
    adx_df = ta.adx(df["High"], df["Low"], df["Close"], length=length)
    if adx_df is None or len(adx_df) < 1: return False
    dmp_col = [c for c in adx_df.columns if c.startswith("DMP")][0]
    dmn_col = [c for c in adx_df.columns if c.startswith("DMN")][0]
    return adx_df[dmp_col].iloc[-1] > adx_df[dmn_col].iloc[-1]

def is_di_bearish(df: pd.DataFrame, length: int = 14) -> bool:
    """Helper: -DI > +DI"""
    if len(df) < length * 2: return False
    adx_df = ta.adx(df["High"], df["Low"], df["Close"], length=length)
    if adx_df is None or len(adx_df) < 1: return False
    dmp_col = [c for c in adx_df.columns if c.startswith("DMP")][0]
    dmn_col = [c for c in adx_df.columns if c.startswith("DMN")][0]
    return adx_df[dmn_col].iloc[-1] > adx_df[dmp_col].iloc[-1]

def is_price_above_sma(df: pd.DataFrame, length: int = 20) -> bool:
    """Helper: Close Price > SMA"""
    if len(df) < length: return False
    sma_s = ta.sma(df["Close"], length=length)
    if sma_s is None or len(sma_s) < 1: return False
    return df["Close"].iloc[-1] > sma_s.iloc[-1]

def is_price_below_sma(df: pd.DataFrame, length: int = 20) -> bool:
    """Helper: Close Price < SMA"""
    if len(df) < length: return False
    sma_s = ta.sma(df["Close"], length=length)
    if sma_s is None or len(sma_s) < 1: return False
    return df["Close"].iloc[-1] < sma_s.iloc[-1]

def is_price_below_ema(df: pd.DataFrame, length: int = 50) -> bool:
    """Helper: Close Price < EMA"""
    if len(df) < length: return False
    ema_s = ta.ema(df["Close"], length=length)
    if ema_s is None or len(ema_s) < 1: return False
    return df["Close"].iloc[-1] < ema_s.iloc[-1]

def is_ema_pco(df: pd.DataFrame, short_len: int = 5, long_len: int = 13) -> bool:
    """Helper: Short EMA > Long EMA (Positive Crossover State)"""
    if len(df) < long_len: return False
    ema_s = ta.ema(df["Close"], length=short_len)
    ema_l = ta.ema(df["Close"], length=long_len)
    if ema_s is None or ema_l is None: return False
    return ema_s.iloc[-1] > ema_l.iloc[-1]

def is_ema_nco(df: pd.DataFrame, short_len: int = 5, long_len: int = 13) -> bool:
    """Helper: Short EMA < Long EMA (Negative Crossover State)"""
    if len(df) < long_len: return False
    ema_s = ta.ema(df["Close"], length=short_len)
    ema_l = ta.ema(df["Close"], length=long_len)
    if ema_s is None or ema_l is None: return False
    return ema_s.iloc[-1] < ema_l.iloc[-1]

def is_volume_above_average(df: pd.DataFrame, length: int = 20) -> bool:
    """Helper: Current Volume > Average Volume OR > preceding 5 candles max"""
    if len(df) < length: return False
    vol_sma = ta.sma(df["Volume"], length=length)
    if vol_sma is None or len(vol_sma) < 1: return False
    
    curr_vol = df["Volume"].iloc[-1]
    
    # Condition 1: Exceeds 20 SMA
    if curr_vol > vol_sma.iloc[-1]: 
        return True
        
    # Condition 2: Exceeds the max volume of precisely the last 5 days
    if len(df) >= 6:
        max_prev_5 = df["Volume"].iloc[-6:-1].max()
        if curr_vol > max_prev_5:
            return True
            
    return False
    
def is_macd_up(df: pd.DataFrame) -> bool:
    """Generic State: MACD is PCO OR MACD is Rising"""
    return is_macd_pco(df) or is_macd_rising(df)

def is_macd_down(df: pd.DataFrame) -> bool:
    """Generic State: MACD is NCO OR MACD is Declining"""
    return is_macd_nco(df) or is_macd_declining(df)

def is_bkp(df: pd.DataFrame) -> bool:
    """Helper: Babaji Ka Prasad (Lower BB Floor/Rounding Bottom)"""
    if len(df) < 20: return False
    bb_df = ta.bbands(df["Close"], length=20, std=2)
    if bb_df is None or len(bb_df) < 2: return False
    l_col = [c for c in bb_df.columns if c.startswith("BBL")][0]
    return bb_df[l_col].iloc[-1] >= bb_df[l_col].iloc[-2]

def is_bkt(df: pd.DataFrame) -> bool:
    """Helper: Bapu Ka Tapli (Upper BB Ceiling)"""
    if len(df) < 20: return False
    bb_df = ta.bbands(df["Close"], length=20, std=2)
    if bb_df is None or len(bb_df) < 2: return False
    u_col = [c for c in bb_df.columns if c.startswith("BBU")][0]
    return bb_df[u_col].iloc[-1] <= bb_df[u_col].iloc[-2]

def is_stoch_pco(df: pd.DataFrame) -> bool:
    """Helper: Stochastic is currently flowing in PCO State"""
    if len(df) < 20: return False
    stoch_d = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_d is None or len(stoch_d) < 1: return False
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    return k.iloc[-1] > d.iloc[-1]

def is_stoch_nco(df: pd.DataFrame) -> bool:
    """Helper: Stochastic is currently flowing in NCO State"""
    if len(df) < 20: return False
    stoch_d = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_d is None or len(stoch_d) < 1: return False
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    return k.iloc[-1] < d.iloc[-1]

def is_solid_candle(df: pd.DataFrame, direction: str = 'bullish', adr_length: int = 20) -> bool:
    """Helper: Solid Candle (Not Tiny, Not Neutral)"""
    if len(df) < adr_length: return False
    adr_df = pd.DataFrame({"tr": df["High"] - df["Low"]})
    adr = adr_df["tr"].rolling(window=adr_length).mean().iloc[-1]
    
    c_open, c_high, c_low, c_close = df["Open"].iloc[-1], df["High"].iloc[-1], df["Low"].iloc[-1], df["Close"].iloc[-1]
    candle_range = c_high - c_low
    
    if candle_range < (0.5 * adr): return False
    real_body = abs(c_open - c_close)
    if real_body < (0.51 * candle_range): return False
        
    return c_close > c_open if direction == 'bullish' else c_close < c_open

def is_stochastic_sell(df: pd.DataFrame, strict_crossover: bool = True) -> bool:
    """Helper: Stochastic Sell Signal (Overbought -> NCO or Crossing Now)"""
    if len(df) < 20: return False
    stoch_d = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_d is None or len(stoch_d) < 3: return False
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    
    # Needs to have been overbought recently
    overbought = (k.iloc[-1] > 70) or (k.iloc[-2] > 70) or (k.iloc[-3] > 70)
    if not overbought: return False
    
    if strict_crossover:
        # Crossed exactly today
        return (k.iloc[-1] < d.iloc[-1]) and (k.iloc[-2] >= d.iloc[-2])
    else:
        return k.iloc[-1] < d.iloc[-1]

def is_stoch_oversold_waiting(df: pd.DataFrame, threshold: int = 30) -> bool:
    """Helper: Stochastic is heavily oversold (K < threshold) and waiting to cross up (K <= D)"""
    if len(df) < 20: return False
    stoch_d = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_d is None or len(stoch_d) < 2: return False
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    return (k.iloc[-1] < threshold) and (k.iloc[-1] <= d.iloc[-1])

def is_stoch_overbought_waiting(df: pd.DataFrame, threshold: int = 70) -> bool:
    """Helper: Stochastic is heavily overbought (K > threshold) and waiting to cross down (K >= D)"""
    if len(df) < 20: return False
    stoch_d = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch_d is None or len(stoch_d) < 2: return False
    k = stoch_d["STOCHk_14_3_3"]
    d = stoch_d["STOCHd_14_3_3"]
    return (k.iloc[-1] > threshold) and (k.iloc[-1] >= d.iloc[-1])
