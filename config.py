# Minimum Average Daily Range (Volatility). Any stock below this is ignored globally across all strategies.
MIN_ADR_PERCENT = 4.0

# -----------------------------------------------------
# MASTER STRATEGY TOGGLES
# -----------------------------------------------------
# Set any strategy to False to instantly disable it from running.
STRATEGIES = {
    # Core Trend Screeners
    "Bullish_TS_Daily": True,
    "Bearish_TS_Daily": True,
    "Bullish_TS_Hourly": False,
    "Bearish_TS_Hourly": False,
    "Bullish_FUT": True,
    "Bearish_FUT": True,
    
    # 4OS Strategies
    "Bullish_4os": True,
    "Bearish_4os": True,
    
    # Momentum & Hooks
    "Bullish_Catalyst": True,
    "Bullish_Hook": True,
    "Bearish_Hook": True
}
