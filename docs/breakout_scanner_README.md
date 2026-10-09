# Large-Base Breakout Scanner

Finds US stocks that broke out of a long base on very heavy volume within the last N days (default 30).

File: `breakout_scanner.py` (single file, no config needed)

---

## Quick start

```bash
pip install yfinance pandas numpy
python breakout_scanner.py
```

First full run takes roughly 10-25 minutes. Output is a table on screen plus a CSV (`breakouts_YYYYMMDD_HHMM.csv`).

Quick test on a few tickers:

```bash
python breakout_scanner.py --tickers NVDA,RKLB,HOOD,PLTR
```

---

## Screening rules

| # | Rule | Default |
|---|------|---------|
| 1 | Breakout-day volume vs prior 20-day average | at least 3x |
| 2 | Close on breakout day | above $1 |
| 3 | Base length (sessions since any bar traded above the breakout close) | at least 126 trading days (~6 months) |
| 4 | Close above every high of the base | required |
| 5 | Up day (close above previous close) | required |
| 6 | Base depth (high to low inside the base) | at most 70% |
| 7 | Breakout date | within last 30 calendar days |

### Volume rank tag (`vol_rank`)

| Tag | Meaning |
|-----|---------|
| `ALL-TIME` | Highest volume in the stock's full available history. For a recent IPO this equals "highest since IPO". |
| `1-YEAR` | Highest volume in the past 252 sessions. |
| `-` | Neither. Still listed unless `--strict` is used. |

`vol_highest_since` shows the last date volume was at or above the breakout-day volume.

Results are sorted: `ALL-TIME`, then `1-YEAR`, then others, and within each tier by volume multiple (highest first).

---

## How it works

1. **Universe:** downloads NASDAQ Trader symbol lists (NASDAQ, NYSE, AMEX). Removes ETFs, test issues, warrants, units, rights and preferreds.
2. **Stage 1:** pulls 2 years of daily data in batches and flags candidates that pass the rules.
3. **Stage 2:** re-pulls full history for the candidates only, to get the true base length and the all-time / since-IPO volume rank.
4. **Output:** prints a table, saves a CSV.

---

## Options

| Option | Default | Purpose |
|--------|---------|---------|
| `--days` | 30 | Breakout must be within last N calendar days |
| `--vol-mult` | 3.0 | Minimum volume multiple vs 20-day average |
| `--min-price` | 1.0 | Minimum close on breakout day |
| `--min-base-days` | 126 | Minimum base length in trading days (252 = 12 months) |
| `--max-depth` | 0.70 | Maximum base depth as a fraction. Use `1.0` to disable |
| `--min-dollar-vol` | 0 | Minimum 20-day average dollar volume, to skip illiquid names |
| `--strict` | off | Keep only `ALL-TIME` or `1-YEAR` volume highs |
| `--tickers` | none | Comma-separated list, skips universe download |
| `--tickers-file` | none | Text file, one ticker per line |
| `--batch` | 150 | Tickers per download batch |
| `--pause` | 0.5 | Seconds between batches |
| `--out` | auto | CSV output filename |

### Example runs

```bash
python breakout_scanner.py --strict
python breakout_scanner.py --min-base-days 252 --strict
python breakout_scanner.py --days 90 --min-dollar-vol 1000000
python breakout_scanner.py --max-depth 1.0 --vol-mult 5
```

---

## Output columns

| Column | Meaning |
|--------|---------|
| `ticker`, `name` | Symbol and company name |
| `breakout_date` | First qualifying day in the window |
| `close`, `day_chg_%` | Breakout-day close and percent change |
| `volume`, `avg20_vol`, `vol_x_avg20` | Breakout-day volume, prior 20-day average, and the multiple |
| `vol_rank`, `vol_highest_since` | Volume rank tag and last date volume was this high |
| `base_sessions`, `base_months` | Base length (months = sessions / 21) |
| `base_hits_data_start` | `True` means price made a new all-time high, so base length is a floor |
| `base_depth_%` | Depth of the base |
| `last_close`, `since_breakout_%` | Latest close and move since breakout day |
| `history_start`, `history_bars` | How much history exists (short = recent IPO) |

---

## Limitations

- Data comes from Yahoo Finance via `yfinance`. It is free and unofficial, and can have gaps, delays or bad volume prints. Verify on your own charts.
- Only the first qualifying day per stock in the window is reported.
- "Since IPO" is inferred from the start of available history. It can't tell a true IPO from a stock that simply has limited data.
- Base length is measured against the breakout-day close, so a stock that spiked above its base earlier and fell back can show a shorter base than you would draw by eye.
- If you get zero results, loosen filters: `--days 60`, `--min-base-days 100`, `--max-depth 1.0`.

Not investment advice.
