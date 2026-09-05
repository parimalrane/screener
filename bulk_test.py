import yfinance as yf
import requests
import pandas as pd
import time

def test_bulk():
    print("Fetching tickers...")
    data = requests.get('https://www.sec.gov/files/company_tickers.json', headers={'User-Agent': 'Mozilla/5.0'}).json()
    tickers = [v['ticker'] for v in data.values()][:2000] # test with 2000
    print(f"Downloading data for {len(tickers)} tickers...")
    start = time.time()
    df = yf.download(tickers, period='6mo', progress=False)
    print(f"Downloaded in {time.time() - start:.1f}s")
    print(f"Close shape: {df['Close'].shape}")
    
    # Vectorized filtering
    valid_tickers = []
    closes = df['Close']
    volumes = df['Volume']
    highs = df['High']
    lows = df['Low']
    
    last_close = closes.iloc[-1]
    avg_vol = volumes.tail(20).mean()
    adr = ((highs - lows) / closes * 100).tail(20).mean()
    
    # weekly volatility
    # resample to weekly
    weekly_closes = closes.resample('W-FRI').last()
    weekly_returns = weekly_closes.pct_change()
    weekly_vol = weekly_returns.tail(20).std() * 100
    
    mask = (last_close > 10) & (avg_vol > 1_000_000) & ((adr > 4.0) | (weekly_vol > 4.0))
    shortlist = mask[mask].index.tolist()
    print(f"Shortlisted: {len(shortlist)} tickers")

if __name__ == "__main__":
    test_bulk()
