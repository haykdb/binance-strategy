# config.py

# Symbol and Trading
SYMBOLS = ["ETHUSDT", "XRPUSDT", "SOLUSDT"]
CAPITAL_PER_TRADE = 300  # USD
USE_TESTNET = True
ALLOW_SHORT_SPREAD = False
LEVERAGE = 1

# Strategy parameters
STRATEGY_LOOKBACK = 60      # in minutes
STRATEGY_Z_ENTRY = 1.5
STRATEGY_Z_EXIT = 0.5
STRATEGY_SLEEP = 1
TC = 0.000001

# Logging
TRADE_LOG_PATH = "analytics/{symbol}_{t:%Y-%m-%d}_trades.csv"
