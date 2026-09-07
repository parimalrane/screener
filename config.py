# Minimum Average Daily Range (Volatility). Any stock below this is ignored globally across all strategies.
MIN_ADR_PERCENT = 4.0

# -----------------------------------------------------
# MASTER STRATEGY TOGGLES
# -----------------------------------------------------
# Set any strategy to False to instantly disable it from running.
STRATEGIES = {
    "Bullish_TS_Daily": True,
    "Bearish_TS_Daily": True,
    "Bullish_MOM": False,
    "Bearish_MOM": False,
    "Bullish_TS_Hourly": True,
    "Bearish_TS_Hourly": True,
    "Bullish_Swing": False,
    "Bearish_Swing": False
}
