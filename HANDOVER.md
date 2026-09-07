# ASTA Algorithmic Screener - Project Handover

## Project State: V3.0 (Institutional Grade)
The ASTA Algorithmic Screener engine is complete, mechanically robust, and perfectly harmonized with the official proprietary ASTA documentation. The entire tag-based scoring legacy system has been annihilated in favor of a strictly categorized binary output system (`High` vs `Medium`).

### Key Architectural Accomplishments
1. **The Taxonomy (`ASTA_Taxonomy.md`):** Complete conceptual definitions translating visual charting heuristics into strict algorithms.
2. **The Quantitative Library (`asta_conditions.py`):** Holds over 20 proprietary helper functions including Bollinger Structural checks (`BBUC`, `BBDC`, `BKP`), unified MACD trajectories, ADX Ungali flow (curling > 12), and rigorous Stochastic flow states.
3. **Execution Pipeline (`main.py`):** 
    - Output is condensed into highly-dense terminal abbreviations (`BU_TS`, `BU_MO`, `BU_SW`, `BE_TS`, `BE_MO`, `BE_SW`) and probability tags (`H` / `M`).
    - Outputs are mathematically sorted by: Direction -> Strategy -> Probability.
    - Historical CSV database is safeguarded automatically against Git merge conflicts or manual file corruptions via instant-rebuild blocks.
4. **Simplistic Local Boot:** Run strictly via `main.bat`.

### Strategy Modules Finalized
All strategy modules evaluate strict parameter sets and return a clean tuple containing `(is_hit, "High"/"Medium")`.

*   **Momentum (`Bullish_MOM` & `Bearish_MOM`):** Captures explosive trend structures. Must clear a 10-point mathematical baseline (including ADX Ungali and Volume). Grades as `High` if Weekly MACD > 0, Daily RSI > 60, and Price is > 50 EMA.
*   **Triple Screen (`Bullish_TS_Daily` & `Bearish_TS_Daily`):** Hunts Mid-Term pullbacks. Inherently assumes `High` probability based purely on the survival of extreme mathematical constraints across 3 timeframes (Monthly PCO, Weekly NCO, Daily Stoch `< 30` Rebound).
*   **Swing Trader (`Bullish_Swing` & `Bearish_Swing`):** Hunts horizontal Double Bottom / BB Floor support bounds (`BKP`). Relies on BBDNC macro structures. Modifies to `High` explicitly if the Stochastic entry springs strictly from the extreme oversold bounds.

## Immediate Roadmap (Next Session)
The mechanical screening engine is considered 100% stable, structurally robust, and strictly institutional. 
Future sessions should strictly focus on:
1. Adding new strategy plugins for lower-timeframe tactical scanning (e.g., Triple Screen Hourly, Intraday Volume spikes).
2. Implementing a quantitative backtesting engine using the generalized `.check` modules to calculate true win rates for `H` vs `M` setups.

## Version History & Architectural Evolution (For Context)
*To assist any future AI agent or developer stepping into this project, here is the historical evolution of the engine to provide context on why the code is structured the way it is:*

* **V1.0 - The Initial Translation:** Converted visual, discretionary ASTA charting manuals into strict Pandas/TA mathematical primitives (`asta_conditions.py`). 
* **V2.0 - Dashboard Harmonization:** Built the core execution engine (`main.py`). Originally utilized a verbose visual "Tagging" system (returning string characters like `*` for BKP bounces or `^` for Tide alignments) to quickly print "setup bonuses" to the screen. 
* **V3.0 - Institutional Upgrade (Current):** Completely annihilated the legacy `<tags>` system. Moved the engine to strict binary Probability scoring (`High` vs `Medium`). Condensed the heavy output strings into rigid 5-letter abbreviations (e.g., `BU_MO`, `BE_SW`) and grouped the terminal sorting exactly by strategy hierarchy. Added a bulletproof auto-recovery block to the CSV database to prevent parsing crashes from external interference.
