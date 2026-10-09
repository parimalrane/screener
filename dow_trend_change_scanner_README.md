# Dow Theory Trend-Change Scanner

Finds US stocks whose primary trend has just changed from **downtrend to uptrend** under Dow Theory, on **weekly** and/or **monthly** bars.

File: `dow_trend_change_scanner.py` (single file)

---

## Quick start

```bash
pip install yfinance pandas numpy
python dow_trend_change_scanner.py                      # weekly (default)
python dow_trend_change_scanner.py --timeframe monthly
python dow_trend_change_scanner.py --timeframe both     # stocks on both rank higher
python dow_trend_change_scanner.py --watch              # also show pre-trigger setups
python dow_trend_change_scanner.py --tickers INTC,PYPL,NKE,BA   # quick test
```

A full run takes roughly 5-15 minutes per timeframe. Output: table on screen plus a CSV.

---

## Dow Theory rules as coded

| Step | Rule |
|------|------|
| Swing pivots | A swing high/low is the extreme of N bars on each side (weekly N=3, monthly N=2), confirmed only after those N bars. Pivots alternate high/low. |
| Downtrend | Last 2 swing highs are each lower than the one before (2 lower highs) and last 2 swing lows are each lower than the one before (2 lower lows). |
| Long-term | Decline from the major peak to the last lower low is at least 30% and at least 26 weeks (monthly: 12 months). |
| Higher low | The pullback after the last lower high (H_c) stays above the last lower low (L_b). |
| Higher high / trigger | A bar **closes** above H_c, the last lower high. |
| Still valid | Price has not traded back below the higher low since the trigger. |
| Volume | Trigger-bar volume vs prior 20-bar average is reported. Require it with `--min-vol-x 1.5`, for example. |

### Status

| Status | Meaning |
|--------|---------|
| `CONFIRMED` | Higher low held and a bar closed above the last lower high, within the lookback window. |
| `WATCH` | Only with `--watch`. Higher low in place, price within 5% below the trigger level, not yet broken. |

---

## Options

| Option | Default | Purpose |
|--------|---------|---------|
| `--timeframe` | weekly | `weekly`, `monthly` or `both` |
| `--lower-highs` | 2 | Consecutive lower highs required |
| `--lower-lows` | 2 | Consecutive lower lows required |
| `--min-drawdown` | 0.30 | Minimum decline from major peak to last low |
| `--min-down-bars` | 26 wk / 12 mo | Minimum length of the downturn |
| `--peak-lookback` | 260 wk / 84 mo | How far back to search for the major peak |
| `--pivot` | 3 wk / 2 mo | Bars each side for swing pivots |
| `--lookback` | 26 wk / 9 mo | Trigger must be within the last N bars |
| `--min-vol-x` | 0 (off) | Required volume multiple on trigger bar |
| `--min-price` | 1.0 | Minimum last close |
| `--watch`, `--watch-pct` | off, 0.05 | Include pre-trigger setups |
| `--include-partial` | off | Use the unfinished current week/month bar |
| `--tickers`, `--tickers-file` | none | Skip universe download |
| `--out` | auto | CSV filename |

### Tuning

```bash
python dow_trend_change_scanner.py --lookback 13                 # fresher changes only (last ~3 months)
python dow_trend_change_scanner.py --min-drawdown 0.5 --min-vol-x 1.5   # deeper, volume-confirmed
python dow_trend_change_scanner.py --lower-lows 1 --lower-highs 1       # looser downtrend definition
```

---

## Output columns

| Column | Meaning |
|--------|---------|
| `status`, `timeframe` | CONFIRMED or WATCH, and the bar size used |
| `trigger_date`, `trigger_close` | First close above the last lower high |
| `last_lower_high` | The level that had to be cleared |
| `higher_low` | Lowest low between that high and the trigger |
| `last_lower_low` | Final low of the downtrend |
| `major_peak`, `drawdown_%`, `downtrend_months` | Size and length of the prior decline |
| `trigger_vol_x_avg20` | Trigger-bar volume vs prior 20-bar average |
| `vs_trigger_level_%` | Last close vs the trigger level (how extended it is) |
| `also_on` | Timeframes on which the stock qualifies |

---

## Limitations

- Pivot-based trend labelling is rule-based and somewhat subjective. Different pivot sizes can give different answers, so test `--pivot` values.
- Classic Dow Theory also wants confirmation between two indexes. This scanner works per stock only.
- Only completed bars are used by default, so a weekly signal appears after Friday's close and a monthly one after month-end.
- Yahoo data is free and unofficial and can have gaps, bad splits or missing history. Verify on your own charts.
- The scanner returns each stock's most recent qualifying change only.

Not investment advice.
