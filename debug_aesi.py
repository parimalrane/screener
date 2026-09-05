import pandas as pd
import pandas_ta as ta
import yfinance as yf
import traceback

def run_debug():
    try:
        print("Downloading AESI...")
        df_daily = yf.download("AESI", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df_daily.empty:
            print("AESI returned empty dataframe.")
            return

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        resample_rules = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        df_weekly = df_daily.resample("W-FRI").agg(resample_rules).dropna()
        df_monthly = df_daily.resample("ME").agg(resample_rules).dropna()

        print("\n--- BASE METRICS ---")
        current_close = df_daily["Close"].iloc[-1]
        current_open = df_daily["Open"].iloc[-1]
        current_high = df_daily["High"].iloc[-1]
        current_low = df_daily["Low"].iloc[-1]
        current_vol = df_daily["Volume"].iloc[-1]
        sma_vol_20 = df_daily["Volume"].tail(20).mean()
        recent_adr = ((df_daily["High"] - df_daily["Low"]) / df_daily["Close"] * 100).tail(20).mean()

        print(f"Price: {current_close:.2f} (>10?)")
        print(f"SMA Vol 20: {sma_vol_20:,.0f} (>1M?)")
        print(f"Current Vol: {current_vol:,.0f} (> SMA Vol?)")
        print(f"ADR: {recent_adr:.2f}% (> 4.0%?)")

        print("\n--- CROSSOVER & CANDLE logic ---")
        sma50 = ta.sma(df_daily["Close"], length=50)
        prev_close = df_daily["Close"].iloc[-2]
        prev_sma50 = sma50.iloc[-2]
        curr_sma50 = sma50.iloc[-1]
        
        crossed_up = prev_close <= prev_sma50 and current_close > curr_sma50
        print(f"Crossed Up 50SMA? {crossed_up} (PrevClose {prev_close:.2f} <= PrevSMA {prev_sma50:.2f} AND CurrClose {current_close:.2f} > CurrSMA {curr_sma50:.2f})")

        total_range = current_high - current_low
        body_range = current_close - current_open
        body_pct = (body_range / total_range) if total_range > 0 else 0
        print(f"Green Candle? {current_close > current_open} | Solid Body %? {body_pct:.2f} (> 0.50?)")

        print("\n--- RSI Checks ---")
        rsi_d = ta.rsi(df_daily["Close"], length=14)
        rsi_w = ta.rsi(df_weekly["Close"], length=14)
        print(f"Daily RSI: {rsi_d.iloc[-1]:.2f} (> 40?)")
        print(f"Weekly RSI: {rsi_w.iloc[-1]:.2f} (> 40?)")

        print("\n--- BOLLINGER BANDS ---")
        bb_d = ta.bbands(df_daily["Close"], length=20, std=2.0)
        bbl_d = bb_d["BBL_20_2.0"]
        bbu_d = bb_d["BBU_20_2.0"]
        
        d_lower_rising_or_flat = bbl_d.iloc[-1] >= bbl_d.iloc[-2]
        d_upper_rising = bbu_d.iloc[-1] > bbu_d.iloc[-2]
        print(f"Daily BB: Lower Rising/Flat? {d_lower_rising_or_flat}, Upper Rising? {d_upper_rising}")

        bb_w = ta.bbands(df_weekly["Close"], length=20, std=2.0)
        bbl_w = bb_w["BBL_20_2.0"]
        bbu_w = bb_w["BBU_20_2.0"]
        
        w_upper_flat_or_declining = bbu_w.iloc[-1] <= bbu_w.iloc[-2]
        w_lower_declining = bbl_w.iloc[-1] < bbl_w.iloc[-2]
        print(f"Weekly BB: Upper flat/declining? {w_upper_flat_or_declining}, Lower declining? {w_lower_declining}")

    except Exception as e:
        print(traceback.format_exc())

if __name__ == "__main__":
    run_debug()
