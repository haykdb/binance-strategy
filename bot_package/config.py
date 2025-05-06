# config.py



# === Trading Settings ===
SYMBOL = "ETHUSDT"
CAPITAL_PER_TRADE = 100  # USD per trade
LEVERAGE = 1
TC = 0.0004

# === Strategy Settings ===
LOOKBACK = 60  # Rolling window for z-score
Z_ENTRY = 0.5
Z_EXIT = 0.25

# === Risk Settings ===
STOP_LOSS_THRESHOLD = -1000  # USD loss per trade triggers emergency exit

# === Sleep Time Between Checks ===
SLEEP_TIME = 1  # seconds

# === Testnet Mode ===
USE_TESTNET = True

# === History Logger ===
HISTORY_FILE = (
    "/Users/admin/PycharmProjects/BinanceBot/analytics/{symbol}_analytics.csv"
)
