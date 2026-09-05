import concurrent.futures
import io
import pandas as pd
import pandas_ta as ta
import requests
import yfinance as yf

# ---------------------------------------------------------
# 1. UNIVERSE SELECTION
# ---------------------------------------------------------
def get_sp500_tickers() -> list[str]:
    """Scrapes S&P 500 ticker list from Wikipedia with browser headers."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(io.StringIO(response.text))
        tickers = tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
        return sorted(list(set(tickers)))
    except Exception as e:
        print(f"Fallback triggered ({e}). Using liquid tech tickers.")
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "AVGO", "NFLX"]

# ---------------------------------------------------------
# 2. SCREENER EVALUATION LOGIC
# ---------------------------------------------------------
def evaluate_stock(ticker: str) -> dict | None:
    """Evaluates the 8 multi-timeframe rules for a single ticker."""
    try:
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False, auto_adjust=True)
        if df_daily.empty or len(df_daily) < 250:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        # Resample daily to Weekly (Friday close) and Monthly (Month-End)
        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        if len(df_monthly) < 30 or len(df_weekly) < 35:
            return None

        # --- MONTHLY CHECKS ---
        macd_m = ta.macd(df_monthly["Close"], fast=12, slow=26, signal=9)
        rsi_m = ta.rsi(df_monthly["Close"], length=14)
        sma_m = ta.sma(df_monthly["Close"], length=20)

        if macd_m is None or rsi_m is None or sma_m is None:
            return None

        # 1. Monthly MACD Line > Signal
        cond1 = macd_m["MACD_12_26_9"].iloc[-1] > macd_m["MACDs_12_26_9"].iloc[-1]
        # 2. Monthly RSI > 60
        cond2 = rsi_m.iloc[-1] > 60
        # 3. Monthly Close > Monthly SMA(20)
        cond3 = df_monthly["Close"].iloc[-1] > sma_m.iloc[-1]

        if not (cond1 and cond2 and cond3):
            return None

        # --- WEEKLY CHECKS ---
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)

        if macd_w is None or rsi_w is None:
            return None

        # 4. Weekly MACD Line < Signal
        cond4 = macd_w["MACD_12_26_9"].iloc[-1] < macd_w["MACDs_12_26_9"].iloc[-1]
        # 5. Weekly RSI > 40
        cond5 = rsi_w.iloc[-1] > 40

        if not (cond4 and cond5):
            return None

        # --- DAILY CHECKS ---
        macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
        stoch_d = ta.stoch(df_daily["High"], df_daily["Low"], df_daily["Close"], k=14, d=3, smooth_k=3)

        if macd_d is None or stoch_d is None:
            return None

        # 6. Daily MACD Line > 1-day ago MACD Line
        cond6 = macd_d["MACD_12_26_9"].iloc[-1] > macd_d["MACD_12_26_9"].iloc[-2]

        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]

        # 7. Daily Slow Stoch %K crossed above %D today
        cond7 = (k.iloc[-1] > d.iloc[-1]) and (k.iloc[-2] <= d.iloc[-2])
        # 8. 2 days ago Slow Stoch %K < 30
        cond8 = k.iloc[-3] < 30

        if cond6 and cond7 and cond8:
            return {
                "Ticker": ticker,
                "Close": round(float(df_daily["Close"].iloc[-1]), 2),
                "Monthly_RSI": round(float(rsi_m.iloc[-1]), 2),
                "Weekly_RSI": round(float(rsi_w.iloc[-1]), 2),
                "Daily_Stoch_K": round(float(k.iloc[-1]), 2),
                "Daily_Stoch_D": round(float(d.iloc[-1]), 2),
            }

    except Exception:
        return None

    return None

# ---------------------------------------------------------
# 3. RUNNER ENTRY POINT
# ---------------------------------------------------------
def run_scan():
    tickers = get_sp500_tickers()
    total = len(tickers)
    print(f"Scanning {total} tickers across Monthly, Weekly, and Daily timeframes...")

    matches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(evaluate_stock, t): t for t in tickers}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            completed += 1
            res = future.result()
            if res:
                matches.append(res)
                print(f"-> Match found: {res['Ticker']} (Close: ${res['Close']})")
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} scanned...")

    print("\n" + "=" * 50)
    print("SCREENER RESULTS")
    print("=" * 50)
    if matches:
        df_results = pd.DataFrame(matches)
        print(df_results.to_string(index=False))
        df_results.to_csv("screener_results.csv", index=False)
        print("\nResults exported to screener_results.csv")
    else:
        print("No tickers matched all 8 criteria today.")

if __name__ == "__main__":
    run_scan()