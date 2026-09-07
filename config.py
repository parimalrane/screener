# Minimum Average Daily Range (Volatility). Any stock below this is ignored globally across all strategies.
MIN_ADR_PERCENT = 4.0

# -----------------------------------------------------
# MASTER STRATEGY TOGGLES
# -----------------------------------------------------
# Set any strategy to False to instantly disable it from running.
STRATEGIES = {
    "Bullish_TS_Daily": True,
    "Bearish_TS_Daily": True,
    "Bullish_MOM": True,
    "Bullish_TS_Hourly": False,
    "Bearish_TS_Hourly": False,
    "Bearish_Swing": True,
    "Bearish_Swing": True
}
