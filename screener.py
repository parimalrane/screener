import concurrent.futures
import io
import os
import pandas as pd
import pandas_ta as ta
import requests
import yfinance as yf

# ---------------------------------------------------------
# 1. UNIVERSE SELECTION
# ---------------------------------------------------------
def get_sp500_tickers() -> list[str]:
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
# 2. SCREENER DEFINITIONS (ADD NEW SCREENS HERE)
# ---------------------------------------------------------
def check_bullish_ts_daily(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, df_monthly: pd.DataFrame) -> bool:
    """Strategy: Bullish_TS_Daily (Multi-timeframe MACD + RSI + Stochastic)"""
    try:
        # Monthly Checks
        macd_m = ta.macd(df_monthly["Close"], fast=12, slow=26, signal=9)
        rsi_m = ta.rsi(df_monthly["Close"], length=14)
        sma_m = ta.sma(df_monthly["Close"], length=20)
        if macd_m is None or rsi_m is None or sma_m is None:
            return False

        cond1 = macd_m["MACD_12_26_9"].iloc[-1] > macd_m["MACDs_12_26_9"].iloc[-1]
        cond2 = rsi_m.iloc[-1] > 60
        cond3 = df_monthly["Close"].iloc[-1] > sma_m.iloc[-1]
        if not (cond1 and cond2 and cond3):
            return False

        # Weekly Checks
        macd_w = ta.macd(df_weekly["Close"], fast=12, slow=26, signal=9)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        if macd_w is None or rsi_w is None:
            return False

        cond4 = macd_w["MACD_12_26_9"].iloc[-1] < macd_w["MACDs_12_26_9"].iloc[-1]
        cond5 = rsi_w.iloc[-1] > 40
        if not (cond4 and cond5):
            return False

        # Daily Checks
        macd_d = ta.macd(df_daily["Close"], fast=12, slow=26, signal=9)
        stoch_d = ta.stoch(df_daily["High"], df_daily["Low"], df_daily["Close"], k=14, d=3, smooth_k=3)
        if macd_d is None or stoch_d is None:
            return False

        cond6 = macd_d["MACD_12_26_9"].iloc[-1] > macd_d["MACD_12_26_9"].iloc[-2]
        k = stoch_d["STOCHk_14_3_3"]
        d = stoch_d["STOCHd_14_3_3"]
        cond7 = (k.iloc[-1] > d.iloc[-1]) and (k.iloc[-2] <= d.iloc[-2])
        cond8 = k.iloc[-3] < 30

        return cond6 and cond7 and cond8
    except Exception:
        return False

# ---------------------------------------------------------
# 3. STOCK EVALUATOR
# ---------------------------------------------------------
def evaluate_stock(ticker: str) -> list[dict]:
    results = []
    try:
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False, auto_adjust=True)
        if df_daily.empty or len(df_daily) < 250:
            return results

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        if len(df_monthly) < 30 or len(df_weekly) < 35:
            return results

        market_date = df_daily.index[-1].strftime("%Y%m%d")
        close_price = round(float(df_daily["Close"].iloc[-1]), 2)

        # Screen 1: Bullish_TS_Daily
        if check_bullish_ts_daily(df_daily, df_weekly, df_monthly):
            results.append({
                "marketdate": market_date,
                "screener_name": "Bullish_TS_Daily",
                "stock": ticker,
                "closing_price": close_price
            })

        # Future screens can simply be appended here:
        # if check_another_screen(df_daily, df_weekly, df_monthly):
        #     results.append({"marketdate": market_date, "screener_name": "Screen_2", "stock": ticker, "closing_price": close_price})

    except Exception:
        return results

    return results

# ---------------------------------------------------------
# 4. RUNNER & PERSISTENCE
# ---------------------------------------------------------
def run_scan():
    tickers = get_sp500_tickers()
    total = len(tickers)
    print(f"Scanning {total} tickers across registered screeners...")

    all_matches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(evaluate_stock, t): t for t in tickers}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            completed += 1
            res = future.result()
            if res:
                all_matches.extend(res)
                for item in res:
                    print(f"-> Match: {item['screener_name']} | {item['stock']} (${item['closing_price']})")
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} scanned...")

    csv_file = "screener_results.csv"

    if all_matches:
        df_new = pd.DataFrame(all_matches)
        print("\n" + "=" * 50)
        print("NEW SCREENER MATCHES")
        print("=" * 50)
        print(df_new.to_string(index=False))

        # Append and deduplicate if file already exists
        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            df_existing = pd.read_csv(csv_file, dtype={"marketdate": str})
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["marketdate", "screener_name", "stock"], keep="last", inplace=True)
            df_combined.to_csv(csv_file, index=False)
        else:
            df_new.to_csv(csv_file, index=False)

        print(f"\nAppended to {csv_file}")
    else:
        print("\nNo tickers matched criteria today.")
        if not os.path.exists(csv_file):
            pd.DataFrame(columns=["marketdate", "screener_name", "stock", "closing_price"]).to_csv(csv_file, index=False)

if __name__ == "__main__":
    run_scan()