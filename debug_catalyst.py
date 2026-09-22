import yfinance as yf
import pandas as pd
from strategies.bullish_catalyst import check
from asta_conditions import is_bbdnc, is_rsi_above, is_solid_candle

tickers = ["AVAT", "HSDT", "LITS", "NNVC"]

for ticker in tickers:
    print(f"\n--- Checking {ticker} ---")
    df = yf.download(ticker, period="5y", interval="1d", progress=False)
    if df.empty:
        print("No daily data.")
        continue
    
    # ensure flat index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df_weekly = df.resample("W-FRI").agg(resample_rules).dropna()
    df_monthly = df.resample("ME").agg(resample_rules).dropna()
    
    if len(df) < 50 or len(df_weekly) < 20: 
        print("Failed: Length requirements")
        continue
        
    print(f"Monthly Len: {len(df_monthly)}, Weekly Len: {len(df_weekly)}")
    
    if len(df_monthly) >= 20:
        if not is_bbdnc(df_monthly): print("Failed: Monthly is_bbdnc")
        if not is_rsi_above(df_monthly, 40): print("Failed: Monthly RSI")
        
    if not is_bbdnc(df_weekly): print("Failed: Weekly is_bbdnc")
    if not is_rsi_above(df_weekly, 40): print("Failed: Weekly RSI")
    
    current_close = df['Close'].iloc[-1]
    current_open = df['Open'].iloc[-1]
    current_volume = df['Volume'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    avg_volume_50 = df['Volume'].rolling(window=50).mean().iloc[-2]
    
    if current_close <= 1.0: print("Failed: Price > $1")
    if ((current_close - prev_close)/prev_close) < 0.10: print("Failed: Change > 10%. Val:", ((current_close - prev_close)/prev_close))
    if current_volume < 1000000: print("Failed: Volume > 1M. Val:", current_volume)
    if pd.isna(avg_volume_50) or avg_volume_50 <= 0 or current_volume < (avg_volume_50 * 2): print("Failed: RVOL > 2. Val:", (current_volume/avg_volume_50))
    if not is_solid_candle(df, direction='bullish'): print("Failed: Solid Candle")
