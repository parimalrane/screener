# ASTA Algorithmic Screener - Project Handover

## Project State: V3.1 (Institutional Grade)
The ASTA Algorithmic Screener engine is complete, mechanically robust, and perfectly harmonized with the official proprietary ASTA documentation. The entire tag-based scoring legacy system has been annihilated in favor of a strictly categorized binary output system (`High` vs `Medium`).

### Key Architectural Accomplishments
1. **The Taxonomy (`ASTA_Taxonomy.md`):** Complete conceptual definitions translating visual charting heuristics into strict algorithms.
2. **The Quantitative Library (`asta_conditions.py`):** Holds over 20 proprietary helper functions including Bollinger Structural checks (`BBUC`, `BBDC`, `BKP`), unified MACD trajectories, ADX Ungali flow (curling > 12), and rigorous Stochastic flow states.
3. **Execution Pipeline (`main.py`):** 
    - Output is condensed into highly-dense, perfectly aligned 6-character terminal abbreviations (e.g., `BU_TSD`, `BU_TSH`, `BU_MOM`, `BU_SWG`) and probability tags (`H` / `M`).
    - Outputs are mathematically sorted by: Direction -> Exact Strategy Hierarchy -> Probability.
    - An automated **TradingView Watchlist Exporter** string is generated at the bottom of every terminal scan output for effortless copy/pasting.
    - Historical CSV database is safeguarded automatically against Git merge conflicts or manual file corruptions via instant-rebuild blocks.
4. **Simplistic Local Boot:** Run strictly via `main.bat`. Configurations (strategy toggles) managed in `config.py`.

### Strategy Modules Finalized
All strategy modules evaluate strict parameter sets sequentially (Super Tide -> Tide -> Wave -> Ripple) and return a clean tuple `(is_hit, "High"/"Medium")`.

*   **Momentum (`Bullish_MOM` & `Bearish_MOM`):** Captures explosive trend structures. Must clear a 10-point mathematical baseline (including ADX Ungali > 12 curling or > 20 pushing). Grades as `H` if Weekly MACD > 0, Daily RSI > 60, and Price is > 50 EMA.
*   **Triple Screen Daily (`Bullish_TS_Daily` & `Bearish_TS_Daily`):** Hunts Mid-Term pullbacks. Uses Monthly/Weekly/Daily structural mapping.
*   **Triple Screen Hourly (`Bullish_TS_Hourly` & `Bearish_TS_Hourly`):** Hunts Short-Term pullbacks. Inherently skips Ripple calculations for manual validation, acting strictly as a Weekly/Daily macro radar. Both TS setups inherently assume `H` probability baseline. Safe-guarded conditionally to skip Super Tide (Monthly MACD) logic for IPOs under 30 months old.
*   **Swing Trader (`Bullish_Swing` & `Bearish_Swing`):** Hunts horizontal Double Bottom / BB Floor support bounds (`BKP`). Modifies to `H` explicitly if the Stochastic entry springs strictly from the extreme oversold bounds.

## Immediate Roadmap (Next Session)
The mechanical screening engine is considered completely mathematically stable. 
Future sessions should strictly focus on:
1. Connecting live 1H intraday data streams into `main.py` if full automation of the `TS_Hourly` Ripple condition is desired.
2. Implementing a quantitative backtesting engine using the generalized `.check` modules to calculate true win rates for `H` vs `M` setups.

## Version History & Architectural Evolution (For Context)
*To assist any future AI agent or developer stepping into this project, here is the historical context:*

* **V1.0 - Initial Translation:** Converted visual ASTA charting manuals into Pandas/TA mathematical primitives (`asta_conditions.py`). 
* **V2.0 - Dashboard Harmonization:** Built the core execution engine (`main.py`). Originally utilized a verbose visual "Tagging" system (`*`, `^`) to represent setup bonuses.
* **V3.0/3.1 - Institutional Upgrade (Current):** Annihilated legacy tagging. Moved to binary Probability scoring (`High` vs `Medium`). Condensed heavy strings into exact 6-character outputs across 8 full strategies. Implemented dynamic TradingView array generation. Added IPO protections and CSV auto-recovery shields.
