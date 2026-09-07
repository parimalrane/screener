# Avadhut Sathe Trading Academy (ASTA) Algorithmic Taxonomy
**Master Documentation for Quantitative Translation**

This document serves as the absolute baseline definition and python logic translation for the proprietary ASTA Momentum terminology. It is designed to be fed into any LLM or AI coding assistant so it instantly understands how to program the exact multi-timeframe structural charts.

---

## 1. BBUC (Bollinger Band Upper Challenged)
**Concept:** The stock is actively attacking the upper band, and the band is physically yielding/expanding to accommodate the momentum. 
**Mathematical Translation:**
* The Current Candle's Upper Bollinger Band value is strictly greater than the Previous Candle's Upper Bollinger Band `(Current Upper BB > Previous Upper BB)`.
* **Mandatory condition:** Price must be above the 20 SMA `(Current Close > 20 SMA)`. This is required to confirm that the price is in the upper half of the band, ensuring the Upper BB rise is driven by upward momentum rather than just an expansion caused by a declining Lower BB.

## 2. BBUFC (Bollinger Band Upper Failed Challenge)
**Concept:** The price tried to actively push the band higher (e.g., the high of the price pinned on the upper Bollinger Band, acting like a shooting star/inverted hammer candle). However, the upside push failed, signifying clear structural resistance.

**Mathematical Translation (Multi-Candle Narrative):**
1. **The Attack (Pinning the Band):** Over a recent lookback window (typically 1 to 4 candles), the price tested the upside resistance. The `High` of the candle must have pinned or pierced the Upper Bollinger Band `(Current or Recent High >= Upper BB)`.
2. **The Resistance:** Because the attempt failed, the Current Candle's Upper Bollinger Band has stopped rising and is now flat or declining `(Current Upper BB <= Previous Upper BB)`.

---

## 3. BBDC (Bollinger Band Downside Challenged)
**Concept:** The stock is actively attacking the lower band, and the band is physically yielding/expanding downwards to accommodate the downward momentum. 
**Mathematical Translation:**
* The Current Candle's Lower Bollinger Band value is strictly less than the Previous Candle's Lower Bollinger Band `(Current Lower BB < Previous Lower BB)`.
* **Mandatory condition:** Price must be below the 20 SMA `(Current Close < 20 SMA)`. This is required to confirm that the price is in the lower half of the band, ensuring the Lower BB drop is driven by downward momentum rather than just an expansion caused by a rising Upper BB.

---

## 4. BBUNC (Bollinger Band Upside Not Challenged)
**Concept:** The price is not actively attacking the upper band. The upper band is either flat/declining, or if it is rising, it is doing so artificially because of downside volatility rather than upward momentum.

**Mathematical Translation:**
A stock is considered BBUNC if it satisfies **at least one** of the following two conditions:
1. **Upper Band is Yielding/Flat:** The Current Candle's Upper Bollinger Band is less than or equal to the Previous Candle's `(Current Upper BB <= Previous Upper BB)`.
2. **Artificial Expansion:** If the Upper Band is rising `(Current Upper BB > Previous Upper BB)`, the price MUST be in the lower half of the band (`Current Close < 20 SMA`) **AND** the Lower Bollinger Band must be challenged (`Current Lower BB < Previous Lower BB`).

---

## 5. BBDNC (Bollinger Band Downside Not Challenged)
**Concept:** The price is not actively attacking the lower band. The lower band is either flat/rising (yielding), or if it is expanding downwards, it is doing so artificially because of upside volatility rather than downward momentum.

**Mathematical Translation:**
A stock is considered BBDNC if it satisfies **at least one** of the following two conditions:
1. **Lower Band is Yielding/Flat:** The Current Candle's Lower Bollinger Band is greater than or equal to the Previous Candle's `(Current Lower BB >= Previous Lower BB)`.
2. **Artificial Expansion:** If the Lower Band is declining `(Current Lower BB < Previous Lower BB)`, the price MUST be in the upper half of the band (`Current Close > 20 SMA`) **AND** the Upper Bollinger Band must be challenged (`Current Upper BB > Previous Upper BB`).

---

## 6. BKP (Babaji Ka Prasad)
**Concept:** This setup is exclusively applicable to the Lower Bollinger Band. It identifies a structural floor where the lower band has stopped declining and is forming a "rounding bottom" or perfectly "flat" profile, indicating downside momentum exhaustion.

**Mathematical Translation:**
* **Lower Band Floor:** The Current Candle's Lower Bollinger band is flat or rising compared to the previous candle `(Current Lower BB >= Previous Lower BB)`.

---

## 7. BKT (Bapu Ka Tapli)
**Concept:** This setup is exclusively applicable to the Upper Bollinger Band. It identifies a structural ceiling where the upper band has stopped rising and is forming a "rounding top" or perfectly "flat" profile, indicating upside momentum exhaustion and a potential cap on the price.

**Mathematical Translation:**
* **Upper Band Ceiling:** The Current Candle's Upper Bollinger band is flat or declining compared to the previous candle `(Current Upper BB <= Previous Upper BB)`.

---

## 8. BBDFC (Bollinger Band Downside Failed Challenge)
**Concept:** The price tried to actively push the band lower (e.g., the low of the price pinned on the lower Bollinger Band, acting like a hammer candle). However, the downside push failed, signifying clear structural support.

**Mathematical Translation (Multi-Candle Narrative):**
1. **The Attack (Pinning the Band):** Over a recent lookback window (typically 1 to 4 candles), the price tested the downside support. The `Low` of the candle must have pinned or pierced the Lower Bollinger Band `(Current or Recent Low <= Lower BB)`.
2. **The Support:** Because the attempt failed, the Current Candle's Lower Bollinger Band has stopped declining and is now flat or rising `(Current Lower BB >= Previous Lower BB)`.

---

## 9. ADX Ungali (ADX Finger)
**Concept:** Represents a clear surge in structural trend strength. The ADX indicator is either actively curling upwards ("pointing the finger") or is already in a confirmed state of high momentum.

**Mathematical Translation:**
A stock satisfies the ADX Ungali setup if it meets **at least one** of the following two conditions:
1. **Actively Rising (From the floor):** The Current Candle's ADX is strictly greater than the Previous Candle's ADX **AND** is currently above 12 `(Current ADX > Previous ADX AND Current ADX > 12)`.
2. **Elevated Momentum:** The Current Candle's ADX value is structurally high, sitting strictly above 15 `(Current ADX > 15)`.

---

### 10. Solid Candle (Not Neutral or Tiny)
**Concept:** The candle must have genuine structural size (not a tiny, low-volatility day) AND true directional conviction (the bulls/bears maintained control into the close without massive wick rejections).

**Mathematical Translation:**
A candle is considered "Solid Bullish" or "Solid Bearish" if it meets **both** of these conditions:
1. **Not Tiny (ADR Check):** The candle's total range `(High - Low)` must be greater than or equal to **50% of the 20-day Average Daily Range (ADR)**.
2. **Not Neutral (Conviction Check):** The candle's real body `Abs(Open - Close)` must make up at least **51%** of its total range `(High - Low)`. 

*(A **Solid Bullish** candle applies these rules and `Close > Open`. A **Solid Bearish** candle applies these rules and `Close < Open`).*

---

### 11. MACD Momentum Rules
**Concept:** Used to determine both structural trend direction and immediate momentum strength using the MACD indicator.

**Mathematical Translation:**
There are distinct ASTA variations and generalized states for MACD:
1. **MACD Rising / Declining (Trajectory):** The MACD Line itself is actively pushing upwards or downwards `(Current MACD > Previous MACD)` or `(Current MACD < Previous MACD)`.
2. **MACD PCO (Positive Crossover):** The MACD Line is actively sitting above its Signal Line `(Current MACD Line > Current Signal Line)`.
3. **MACD NCO (Negative Crossover):** The MACD Line is actively sitting below its Signal Line `(Current MACD Line < Current Signal Line)`.
4. **MACD UP (Generic Bullish State):** A stock passes this if MACD is EITHER in a PCO state OR actively Rising `(PCO OR Rising)`.
5. **MACD DOWN (Generic Bearish State):** A stock passes this if MACD is EITHER in an NCO state OR actively Declining `(NCO OR Declining)`.

---

### 12. Stochastic Momentum Alignments
**Concept:** Measures the active flowing state of the Stochastic indicator regardless of when the initial crossover trigger happened.

**Mathematical Translation:**
1. **Stochastic PCO (Positive Crossover State):** The fast `%K` line is actively positioned strictly above the slow `%D` signal line `(Current %K > Current %D)`.
2. **Stochastic NCO (Negative Crossover State):** The fast `%K` line is actively positioned strictly below the slow `%D` signal line `(Current %K < Current %D)`.

---

### 13. Stochastic Oversold Buy Signal
**Concept:** A momentum entry trigger used when the stock has dipped into an oversold region and is snapping back up.

**Mathematical Translation:**
A stock triggers a Stochastic Buy Signal if it meets **both** of these conditions:
1. **Oversold:** The Stochastic `%K` line was recently in the oversold region `(%K < 30)`.
2. **Trigger (Crossover or PCO):** The `%K` line has just formally crossed above the `%D` signal line, OR it is already flowing actively in a PCO state `(Current %K > Current %D)`.

---

### 14. Stochastic Overbought Sell Signal
**Concept:** A momentum exit/short trigger used when the stock has pushed into an overbought region and is snapping down.

**Mathematical Translation:**
A stock triggers a Stochastic Sell Signal if it meets **both** of these conditions:
1. **Overbought:** The Stochastic `%K` line was recently in the overbought region `(%K > 70)`.
2. **Trigger (Crossover or NCO):** The `%K` line has just formally crossed below the `%D` signal line, OR it is already flowing actively in an NCO state `(Current %K < Current %D)`.

---

### 15. RSI Momentum Zones & Equator
**Concept:** The ASTA methodology divides RSI into distinct structural zones to confirm overarching momentum, and utilizes the 50 level as the absolute equator.

**Mathematical Translation:**
*   **The Equator (Higher Timeframes):** An RSI `> 50` places the stock in the "Upper Half", offering supportive momentum (often the baseline requirement for Weekly/Monthly charts).
*   **Bullish Momentum:** The Current Candle's RSI is strictly greater than 60 `(Current RSI > 60)`. (Often the strict requirement on the Daily chart).
*   **Bearish Momentum:** The Current Candle's RSI is strictly less than 40 `(Current RSI < 40)`.
*   **Swing (Transition Zone):** The Current Candle's RSI is floating in the middle transition zone `(Current RSI >= 40 AND Current RSI <= 60)`.
