# Minimum Average Daily Range (Volatility). Any stock below this is ignored globally across all strategies.
MIN_ADR_PERCENT = 4.0

# Determines how tight the MACD "Kiss" must be for Hook setups. 
# 0.25 means the gap must shrink to at least 25% of its recent peak.
MACD_HOOK_COMPRESSION = 0.25

# -----------------------------------------------------
# MASTER STRATEGY TOGGLES
# -----------------------------------------------------
# Set any strategy to False to instantly disable it from running.
STRATEGIES = {
    # Core Trend Screeners
    "Bullish_TS_Daily": True,
    "Bearish_TS_Daily": True,
    "Bullish_Daily_2": True,
    "Bearish_Daily_2": True,
    "Bullish_TS_Hourly": False,
    "Bearish_TS_Hourly": False,
    "Bullish_FUT": False,
    "Bearish_FUT": False,
    
    # 4OS Strategies
    "Bullish_4os": True,
    "Bearish_4os": True,
    
    # Momentum & Hooks
    "Bullish_Catalyst": True,
    "Bullish_Hook": False,
    "Bearish_Hook": False,
    
    # Pullbacks
    "Bullish_Pullback": True,
    "Bearish_Pullback": True
}
