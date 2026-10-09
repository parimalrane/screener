#!/usr/bin/env python3
"""
Large-Base Breakout Scanner (US stocks)
=======================================
Finds US stocks that, within the last N days (default 30), broke out of a long
base on very heavy volume.

Rules (all adjustable from the command line):
  1. Breakout-day volume >= 3x the average of the prior 20 sessions
  2. Breakout-day close > $1
  3. Close is above the highest HIGH of the prior base (>= 126 trading days,
     ~6 months, with no bar trading above the breakout close in that window)
  4. Up day (close > previous close)
  5. Volume rank on the breakout day is reported:
       ALL-TIME  = highest volume in the stock's entire history
                   (for a recent IPO this equals "highest since IPO")
       1-YEAR    = highest volume in the past 252 sessions
       none      = neither (still listed unless you use --strict)

Install:   pip install yfinance pandas numpy
Run:       python breakout_scanner.py
Quick test python breakout_scanner.py --tickers NVDA,PLTR,RKLB,HOOD
Strict:    python breakout_scanner.py --strict        (only ALL-TIME / 1-YEAR volume)
Longer:    python breakout_scanner.py --days 90 --min-base-days 252

Data: Yahoo Finance via yfinance (free, unofficial, can be delayed/imperfect).
Universe: NASDAQ Trader symbol directory (all NASDAQ/NYSE/AMEX common stocks).
First full run takes roughly 10-25 minutes. Output: table on screen + CSV file.
Not investment advice. Always verify on your own charts.
"""

import argparse
import io
import sys
import time
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit("Missing dependency. Run:  pip install yfinance pandas numpy")

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
BAD_NAME_WORDS = (
    "warrant", "right", " unit", "preferred", "depositary", "notes due",
    "% notes", "subordinated", "debenture", "trust preferred", "etn",
)


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------
def _read_symdir(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        txt = r.read().decode("utf-8", errors="ignore")
    lines = [ln for ln in txt.splitlines() if not ln.startswith("File Creation Time")]
    return pd.read_csv(io.StringIO("\n".join(lines)), sep="|", dtype=str).fillna("")


def load_universe():
    """Return dict {yahoo_symbol: company_name} for US-listed common stocks."""
    out = {}
    try:
        nd = _read_symdir(NASDAQ_URL)
        nd = nd[(nd["Test Issue"] == "N") & (nd["ETF"] == "N")]
        for sym, name in zip(nd["Symbol"], nd["Security Name"]):
            out[sym] = name
        ot = _read_symdir(OTHER_URL)
        ot = ot[(ot["Test Issue"] == "N") & (ot["ETF"] == "N")]
        for sym, name in zip(ot["ACT Symbol"], ot["Security Name"]):
            out[sym] = name
    except Exception as e:
        sys.exit(f"Could not download symbol lists ({e}). "
                 f"Use --tickers AAPL,MSFT,... or --tickers-file file.txt instead.")
    clean = {}
    for sym, name in out.items():
        s = sym.strip().upper()
        if not s or "$" in s or "^" in s or len(s) > 5 and "." not in s:
            continue
        if any(w in name.lower() for w in BAD_NAME_WORDS):
            continue
        clean[s.replace(".", "-")] = name
    return clean


# --------------------------------------------------------------------------
# Data download
# --------------------------------------------------------------------------
def download_batch(tickers, period, retries=3):
    for attempt in range(retries):
        try:
            data = yf.download(
                tickers, period=period, interval="1d", group_by="ticker",
                auto_adjust=False, threads=True, progress=False, timeout=60,
            )
            if data is not None and len(data):
                return data
        except Exception:
            pass
        time.sleep(2 + attempt * 3)
    return None


def split_frames(data, tickers):
    """Yield (ticker, OHLCV dataframe) from a yfinance batch download."""
    if data is None or data.empty:
        return
    multi = isinstance(data.columns, pd.MultiIndex)
    top = set(data.columns.get_level_values(0)) if multi else set()
    for t in tickers:
        try:
            df = data[t] if multi and t in top else (data if not multi else None)
            if df is None:
                continue
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(
                subset=["Close", "High", "Low", "Volume"])
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)
            if len(df):
                yield t, df
        except Exception:
            continue


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------
def evaluate(df, a):
    """Return a dict for the first qualifying breakout day in the window, else None."""
    if len(df) < 60:
        return None
    o = df["Open"].values.astype(float)
    h = df["High"].values.astype(float)
    l = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    v = df["Volume"].values.astype(float)
    dates = df.index

    avg20 = pd.Series(v).shift(1).rolling(20).mean().values
    cutoff = dates[-1] - pd.Timedelta(days=a.days)
    idxs = np.where(dates >= cutoff)[0]

    for i in idxs:
        if i < 21 or not np.isfinite(avg20[i]) or avg20[i] <= 0:
            continue
        ratio = v[i] / avg20[i]
        if ratio < a.vol_mult or c[i] <= a.min_price or c[i] <= c[i - 1]:
            continue
        if avg20[i] * c[i] < a.min_dollar_vol:
            continue

        # Base length = sessions since any bar last traded ABOVE today's close
        higher = np.where(h[:i] > c[i])[0]
        if len(higher):
            j = higher[-1]
            base_days, capped = i - j - 1, False
        else:
            j, base_days, capped = -1, i, True  # whole history is below -> new ATH
        if base_days < a.min_base_days:
            continue

        base_hi = h[j + 1:i].max()
        base_lo = l[j + 1:i].min()
        depth = 1.0 - base_lo / base_hi if base_hi > 0 else np.nan
        if np.isfinite(depth) and depth > a.max_depth:
            continue

        # Volume rank on breakout day
        prior_max_all = v[:i].max() if i > 0 else 0
        prior_max_1y = v[max(0, i - 252):i].max() if i > 0 else 0
        if v[i] >= prior_max_all:
            rank = "ALL-TIME"
        elif v[i] >= prior_max_1y:
            rank = "1-YEAR"
        else:
            rank = "-"
        bigger = np.where(v[:i] >= v[i])[0]
        since = dates[bigger[-1]].strftime("%Y-%m-%d") if len(bigger) else "never"

        return {
            "breakout_date": dates[i].strftime("%Y-%m-%d"),
            "close": round(c[i], 2),
            "day_chg_%": round((c[i] / c[i - 1] - 1) * 100, 1),
            "volume": int(v[i]),
            "avg20_vol": int(avg20[i]),
            "vol_x_avg20": round(ratio, 1),
            "vol_rank": rank,
            "vol_highest_since": since,
            "base_sessions": int(base_days),
            "base_months": round(base_days / 21, 1),
            "base_hits_data_start": capped,
            "base_depth_%": round(depth * 100, 0) if np.isfinite(depth) else None,
            "last_close": round(c[-1], 2),
            "since_breakout_%": round((c[-1] / c[i] - 1) * 100, 1),
            "history_start": dates[0].strftime("%Y-%m-%d"),
            "history_bars": len(df),
        }
    return None


def run_stage(tickers, period, a, label):
    hits = {}
    n = len(tickers)
    for k in range(0, n, a.batch):
        batch = tickers[k:k + a.batch]
        print(f"  [{label}] {min(k + a.batch, n)}/{n} tickers scanned, "
              f"{len(hits)} candidates so far", end="\r", flush=True)
        data = download_batch(batch, period)
        for t, df in split_frames(data, batch):
            res = evaluate(df, a)
            if res:
                hits[t] = res
        time.sleep(a.pause)
    print(" " * 90, end="\r")
    return hits


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Large-base breakout on heavy-volume scanner")
    p.add_argument("--days", type=int, default=30, help="breakout must be within last N calendar days")
    p.add_argument("--vol-mult", type=float, default=3.0, help="min volume vs prior 20-day avg")
    p.add_argument("--min-price", type=float, default=1.0, help="min close on breakout day")
    p.add_argument("--min-base-days", type=int, default=126, help="min base length in trading days")
    p.add_argument("--max-depth", type=float, default=0.70,
                   help="max base depth as fraction (0.70 = 70%%); use 1.0 to disable")
    p.add_argument("--min-dollar-vol", type=float, default=0.0,
                   help="min 20-day avg dollar volume (e.g. 1000000) to skip illiquid names")
    p.add_argument("--strict", action="store_true",
                   help="only keep ALL-TIME or 1-YEAR volume highs")
    p.add_argument("--tickers", type=str, default="", help="comma-separated list (skip universe download)")
    p.add_argument("--tickers-file", type=str, default="", help="text file, one ticker per line")
    p.add_argument("--batch", type=int, default=150)
    p.add_argument("--pause", type=float, default=0.5)
    p.add_argument("--out", type=str, default="")
    a = p.parse_args()

    names = {}
    if a.tickers:
        tickers = [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
    elif a.tickers_file:
        with open(a.tickers_file) as f:
            tickers = [ln.strip().upper() for ln in f if ln.strip()]
    else:
        print("Downloading US symbol universe...")
        names = load_universe()
        tickers = sorted(names)
    print(f"Universe: {len(tickers)} tickers | window: last {a.days} days | "
          f"vol >= {a.vol_mult}x avg20 | price > ${a.min_price} | base >= {a.min_base_days} sessions")

    # Stage 1: 2 years of data to find candidates quickly
    print("Stage 1: scanning 2-year history...")
    cands = run_stage(tickers, "2y", a, "2y")
    print(f"Stage 1 candidates: {len(cands)}")
    if not cands:
        print("No candidates. Try --days 60, --min-base-days 100, or --max-depth 1.0")
        return

    # Stage 2: full history for candidates -> true base length and volume rank
    print("Stage 2: re-checking candidates on full history (all-time / since-IPO volume)...")
    final = run_stage(sorted(cands), "max", a, "max")

    rows = []
    for t, r in final.items():
        row = {"ticker": t, "name": names.get(t, "")[:38]}
        row.update(r)
        rows.append(row)
    if not rows:
        print("No stocks survived full-history check.")
        return

    df = pd.DataFrame(rows)
    if a.strict:
        df = df[df["vol_rank"].isin(["ALL-TIME", "1-YEAR"])]
    tier = {"ALL-TIME": 0, "1-YEAR": 1, "-": 2}
    df["_t"] = df["vol_rank"].map(tier)
    df = df.sort_values(["_t", "vol_x_avg20"], ascending=[True, False]).drop(columns="_t")

    out = a.out or f"breakouts_{datetime.now():%Y%m%d_%H%M}.csv"
    df.to_csv(out, index=False)

    show = ["ticker", "name", "breakout_date", "close", "day_chg_%", "vol_x_avg20",
            "vol_rank", "vol_highest_since", "base_months", "base_depth_%", "since_breakout_%"]
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 500)
    print(f"\n{len(df)} breakouts found (sorted: ALL-TIME vol > 1-YEAR vol > others, then by volume multiple)\n")
    print(df[show].to_string(index=False))
    print(f"\nSaved: {out}")
    print("Notes: ALL-TIME = highest volume in available history (= since IPO for newer listings). "
          "base_hits_data_start=True means price made a new all-time high.")


if __name__ == "__main__":
    main()
