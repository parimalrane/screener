#!/usr/bin/env python3
"""
Dow Theory Trend-Change Scanner (US stocks, weekly / monthly)
=============================================================
Finds stocks whose PRIMARY trend has just changed from DOWNTREND to UPTREND
according to Dow Theory, measured on weekly and/or monthly bars.

Dow Theory logic used
---------------------
 DOWNTREND  : series of lower swing highs AND lower swing lows
              (default: 2 lower highs + 2 lower lows, on confirmed swing pivots)
 LONG-TERM  : the decline from the major peak must be big and long
              (default weekly: >=30% and >=26 weeks; monthly: >=30% and >=12 months)
 CHANGE     : after the last lower low (L_b) and the last lower high (H_c):
                1) HIGHER LOW   - the pullback after H_c holds ABOVE L_b
                2) HIGHER HIGH  - a bar CLOSES above H_c (the last lower high)
              Both together = Dow-style reversal to uptrend (status CONFIRMED).
 STILL VALID: price has not closed back under the higher low since the trigger.
 WATCH      : (optional) higher low is in place and price is within X% below H_c
              but has not closed above it yet.
 Volume     : reported as trigger-bar volume vs prior 20-bar average
              (Dow: volume should confirm the trend). Use --min-vol-x to require it.

Install:   pip install yfinance pandas numpy
Run:       python dow_trend_change_scanner.py                      (weekly)
           python dow_trend_change_scanner.py --timeframe monthly
           python dow_trend_change_scanner.py --timeframe both
Test:      python dow_trend_change_scanner.py --tickers INTC,PYPL,NKE,BA
Watchlist: python dow_trend_change_scanner.py --watch

Data: Yahoo Finance via yfinance (free, unofficial). Universe: NASDAQ Trader
symbol directory. A full run takes roughly 5-15 minutes per timeframe.
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

# Per-timeframe defaults (overridable from the command line)
TF_DEFAULTS = {
    "weekly":  {"interval": "1wk", "pivot": 3, "lookback": 26, "min_down_bars": 26,
                "peak_lookback": 260, "min_bars": 120},
    "monthly": {"interval": "1mo", "pivot": 2, "lookback": 9, "min_down_bars": 12,
                "peak_lookback": 84, "min_bars": 48},
}


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------
def _read_symdir(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        txt = r.read().decode("utf-8", errors="ignore")
    lines = [ln for ln in txt.splitlines() if not ln.startswith("File Creation Time")]
    return pd.read_csv(io.StringIO("\n".join(lines)), sep="|", dtype=str).fillna("")


def load_universe():
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
        if not s or "$" in s or "^" in s or (len(s) > 5 and "." not in s):
            continue
        if any(w in name.lower() for w in BAD_NAME_WORDS):
            continue
        clean[s.replace(".", "-")] = name
    return clean


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def download_batch(tickers, interval, retries=3):
    for attempt in range(retries):
        try:
            data = yf.download(
                tickers, period="max", interval=interval, group_by="ticker",
                auto_adjust=False, threads=True, progress=False, timeout=60,
            )
            if data is not None and len(data):
                return data
        except Exception:
            pass
        time.sleep(2 + attempt * 3)
    return None


def drop_incomplete_bar(df, tf):
    """Remove the last bar if its week/month has not finished yet."""
    if df.empty:
        return df
    last = df.index[-1]
    today = pd.Timestamp.today().normalize()
    if tf == "weekly":
        # weekly bar is stamped on Monday; it is complete once Friday has passed
        if (today - last).days <= 4:
            return df.iloc[:-1]
    else:
        if last.year == today.year and last.month == today.month:
            return df.iloc[:-1]
    return df


def split_frames(data, tickers, tf, completed_only):
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
                subset=["Close", "High", "Low"])
            df["Volume"] = df["Volume"].fillna(0)
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)
            if completed_only:
                df = drop_incomplete_bar(df, tf)
            if len(df):
                yield t, df
        except Exception:
            continue


# --------------------------------------------------------------------------
# Dow Theory logic
# --------------------------------------------------------------------------
def find_pivots(h, l, n):
    """Confirmed swing pivots (fractal with n bars each side), alternating H/L."""
    N = len(h)
    piv = []
    for i in range(n, N - n):
        is_h = h[i] > h[i - n:i].max() and h[i] >= h[i + 1:i + n + 1].max()
        is_l = l[i] < l[i - n:i].min() and l[i] <= l[i + 1:i + n + 1].min()
        if is_h and is_l:
            continue  # outside bar, ambiguous
        if is_h:
            piv.append((i, "H", float(h[i])))
        elif is_l:
            piv.append((i, "L", float(l[i])))
    alt = []
    for p in piv:
        if alt and alt[-1][1] == p[1]:
            if (p[1] == "H" and p[2] > alt[-1][2]) or (p[1] == "L" and p[2] < alt[-1][2]):
                alt[-1] = p
        else:
            alt.append(p)
    return alt


def strictly_desc(vals):
    return all(vals[j] > vals[j + 1] for j in range(len(vals) - 1))


def analyze(df, a, tf):
    """Return the most recent downtrend->uptrend change (or watch setup), else None."""
    if len(df) < a.min_bars:
        return None
    o = df["Open"].values.astype(float)
    h = df["High"].values.astype(float)
    l = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    v = df["Volume"].values.astype(float)
    dates = df.index
    N = len(df)
    if c[-1] < a.min_price:
        return None

    alt = find_pivots(h, l, a.pivot)
    highs = [p for p in alt if p[1] == "H"]
    lows = [p for p in alt if p[1] == "L"]
    if len(highs) < a.lower_highs + 1 or len(lows) < a.lower_lows + 1:
        return None

    best = None
    for k in range(a.lower_highs, len(highs)):
        hseq = highs[k - a.lower_highs:k + 1]
        if not strictly_desc([x[2] for x in hseq]):
            continue
        Hc = hseq[-1]
        lows_before = [x for x in lows if x[0] < Hc[0]]
        if len(lows_before) < a.lower_lows + 1:
            continue
        lseq = lows_before[-(a.lower_lows + 1):]
        if not strictly_desc([x[2] for x in lseq]):
            continue
        Lb = lseq[-1]

        # Trigger: first CLOSE above the last lower high
        after = c[Hc[0] + 1:]
        hit = np.where(after > Hc[2])[0]
        if len(hit):
            t = Hc[0] + 1 + int(hit[0])
            status = "CONFIRMED"
            if N - 1 - t > a.lookback:
                continue
        else:
            if not a.watch or k != len(highs) - 1:
                continue
            t = None
            status = "WATCH"
        end = t if t is not None else N - 1
        if end <= Hc[0]:
            continue

        # Higher low must hold above the last lower low
        seg_low = l[Hc[0] + 1:end + 1]
        Lc_idx = Hc[0] + 1 + int(np.argmin(seg_low))
        Lc = float(l[Lc_idx])
        if Lc <= Lb[2]:
            continue

        # Size / length of the prior long-term downturn
        lo = max(0, Lb[0] - a.peak_lookback)
        pk = lo + int(np.argmax(h[lo:Lb[0] + 1]))
        peak = float(h[pk])
        drawdown = 1 - Lb[2] / peak
        down_bars = Lb[0] - pk
        if drawdown < a.min_drawdown or down_bars < a.min_down_bars:
            continue

        if status == "CONFIRMED":
            # Trend still valid: higher low not violated since trigger
            if t + 1 < N and l[t + 1:].min() <= Lc:
                continue
            if c[t] < a.min_price:
                continue
            vol_x = None
            if t >= 20 and v[t - 20:t].mean() > 0:
                vol_x = float(v[t] / v[t - 20:t].mean())
            if a.min_vol_x > 0 and (vol_x is None or vol_x < a.min_vol_x):
                continue
        else:
            if c[-1] < (1 - a.watch_pct) * Hc[2]:
                continue
            vol_x = None

        cand = {
            "status": status,
            "timeframe": tf,
            "trigger_date": dates[t].strftime("%Y-%m-%d") if t is not None else "",
            "trigger_close": round(float(c[t]), 2) if t is not None else None,
            "bars_since_trigger": (N - 1 - t) if t is not None else None,
            "trigger_vol_x_avg20": round(vol_x, 1) if vol_x else None,
            "last_lower_high": round(Hc[2], 2),
            "last_lower_high_date": dates[Hc[0]].strftime("%Y-%m-%d"),
            "higher_low": round(Lc, 2),
            "higher_low_date": dates[Lc_idx].strftime("%Y-%m-%d"),
            "last_lower_low": round(Lb[2], 2),
            "last_lower_low_date": dates[Lb[0]].strftime("%Y-%m-%d"),
            "major_peak": round(peak, 2),
            "major_peak_date": dates[pk].strftime("%Y-%m-%d"),
            "drawdown_%": round(drawdown * 100, 0),
            "downtrend_bars": int(down_bars),
            "downtrend_months": round(down_bars / (4.345 if tf == "weekly" else 1), 1),
            "last_close": round(float(c[-1]), 2),
            "vs_trigger_level_%": round((c[-1] / Hc[2] - 1) * 100, 1),
        }
        key = t if t is not None else N
        if best is None or key > best[0]:
            best = (key, cand)
    return best[1] if best else None


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
def run_timeframe(tickers, tf, a, names):
    cfg = TF_DEFAULTS[tf]
    local = argparse.Namespace(**vars(a))
    for key in ("pivot", "lookback", "min_down_bars", "peak_lookback", "min_bars"):
        if getattr(a, key) is None:
            setattr(local, key, cfg[key])
    rows = []
    n = len(tickers)
    for k in range(0, n, a.batch):
        batch = tickers[k:k + a.batch]
        print(f"  [{tf}] {min(k + a.batch, n)}/{n} scanned, {len(rows)} found",
              end="\r", flush=True)
        data = download_batch(batch, cfg["interval"])
        for t, df in split_frames(data, batch, tf, not a.include_partial):
            res = analyze(df, local, tf)
            if res:
                row = {"ticker": t, "name": names.get(t, "")[:38]}
                row.update(res)
                rows.append(row)
        time.sleep(a.pause)
    print(" " * 80, end="\r")
    return rows


def main():
    p = argparse.ArgumentParser(description="Dow Theory downtrend->uptrend change scanner")
    p.add_argument("--timeframe", choices=["weekly", "monthly", "both"], default="weekly")
    p.add_argument("--lower-highs", type=int, default=2, help="min consecutive lower highs in downtrend")
    p.add_argument("--lower-lows", type=int, default=2, help="min consecutive lower lows in downtrend")
    p.add_argument("--min-drawdown", type=float, default=0.30,
                   help="min decline from major peak to last low (0.30 = 30%%)")
    p.add_argument("--min-down-bars", type=int, default=None,
                   help="min bars from peak to last low (weekly 26 / monthly 12)")
    p.add_argument("--peak-lookback", type=int, default=None, help="bars to search for the major peak")
    p.add_argument("--pivot", type=int, default=None, help="bars each side for swing pivots (weekly 3 / monthly 2)")
    p.add_argument("--lookback", type=int, default=None,
                   help="trigger must be within last N bars (weekly 26 / monthly 9)")
    p.add_argument("--min-bars", type=int, default=None, help="min history in bars")
    p.add_argument("--min-price", type=float, default=1.0)
    p.add_argument("--min-vol-x", type=float, default=0.0,
                   help="require trigger-bar volume >= X times prior 20-bar average (0 = off)")
    p.add_argument("--watch", action="store_true", help="also list pre-trigger WATCH setups")
    p.add_argument("--watch-pct", type=float, default=0.05, help="WATCH: within this fraction below trigger level")
    p.add_argument("--include-partial", action="store_true",
                   help="use the current unfinished week/month bar (default: completed bars only)")
    p.add_argument("--tickers", type=str, default="")
    p.add_argument("--tickers-file", type=str, default="")
    p.add_argument("--batch", type=int, default=100)
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

    tfs = ["weekly", "monthly"] if a.timeframe == "both" else [a.timeframe]
    print(f"Universe: {len(tickers)} tickers | timeframe: {a.timeframe} | "
          f"downtrend: {a.lower_highs} lower highs + {a.lower_lows} lower lows, "
          f">= {a.min_drawdown:.0%} drawdown")

    rows = []
    for tf in tfs:
        print(f"Scanning {tf} bars...")
        rows += run_timeframe(tickers, tf, a, names)

    if not rows:
        print("No trend changes found. Try --lookback 52 (weekly), --min-drawdown 0.2, "
              "--lower-lows 1, or --watch.")
        return

    df = pd.DataFrame(rows)
    df["also_on"] = df.groupby("ticker")["timeframe"].transform(lambda s: "+".join(sorted(set(s))))
    order = {"CONFIRMED": 0, "WATCH": 1}
    df["_s"] = df["status"].map(order)
    df["_n"] = df["also_on"].str.count(r"\+")
    df = df.sort_values(["_s", "_n", "trigger_date"], ascending=[True, False, False]).drop(columns=["_s", "_n"])

    out = a.out or f"dow_trend_change_{datetime.now():%Y%m%d_%H%M}.csv"
    df.to_csv(out, index=False)

    show = ["ticker", "name", "timeframe", "status", "trigger_date", "trigger_close",
            "last_lower_high", "higher_low", "last_lower_low", "drawdown_%",
            "downtrend_months", "trigger_vol_x_avg20", "vs_trigger_level_%", "also_on"]
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.max_rows", 500)
    print(f"\n{len(df)} setups found (CONFIRMED first; stocks on both timeframes ranked higher)\n")
    print(df[show].to_string(index=False))
    print(f"\nSaved: {out}")
    print("CONFIRMED = higher low held + close above last lower high, higher low still intact. "
          "WATCH = higher low in place, price within reach of the trigger level.")


if __name__ == "__main__":
    main()
