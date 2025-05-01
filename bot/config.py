# config.py

# === Spot Testnet API Settings ===
SPOT_API_KEY = "iVbyH2SVnWUAd1wyYPzW6CuX6OcYtZKH0m2u4yac8G9FA45OtdmJqohrtz9ZgT8x"
SPOT_API_SECRET = "1t9kHnXsj3fS8VadntJIdu8JqGqg5CFvfE6Q5x5pOac46rzk8XnBaDwKGoNaYTaI"

# === Futures Testnet API Settings ===
FUTURES_API_KEY = "76b91893df17578be29428909d8907eeabae12b26966c508844e5a2b29b69a5e"
FUTURES_API_SECRET = "755d61406a815b5ef7030b1bdbdf14c2f676e8ae28dfbe487fb73991bbb39fd3"

# === Trading Settings ===
SYMBOL = "ONTUSDT"
CAPITAL_PER_TRADE = 100  # USD per trade
LEVERAGE = 1
TC = 0.0004

# === Strategy Settings ===
LOOKBACK = 120  # Rolling window for z-score
Z_ENTRY = 1.5
Z_EXIT = 0.5

# === Risk Settings ===
STOP_LOSS_THRESHOLD = -1000  # USD loss per trade triggers emergency exit

# === Sleep Time Between Checks ===
SLEEP_TIME = 0.2  # seconds

# === Testnet Mode ===
USE_TESTNET = True

# === History Logger ===
HISTORY_FILE = "/Users/admin/PycharmProjects/BinanceBot/analytics/{symbol}_analytics.csv"