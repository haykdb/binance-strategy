# main.py

import threading
import multiprocessing as mp
import final_config as config
import config as api_configs
from loguru import logger
from binance.client import Client
from datetime import date
from final_bot import Bot
from status_store import symbol_status
from live_monitor import LiveMonitor

LOGGER = f"/Users/admin/PycharmProjects/binance-strategy/logs/{date.today()}.log"
logger.add(LOGGER)

# === CONNECT ===

SPOT_CLIENT = Client(
    api_configs.SPOT_API_KEY, api_configs.SPOT_API_SECRET, testnet=config.USE_TESTNET
)
FUTURES_CLIENT = Client(
    api_configs.FUTURES_API_KEY, api_configs.FUTURES_API_SECRET, testnet=config.USE_TESTNET
)

def run_bot(symbol: str):
    """Initializes and runs a bot instance for a given symbol."""

    # === MANUALLY SET TESTNET URLs ===
    if config.USE_TESTNET:
        SPOT_CLIENT.API_URL = "https://testnet.binance.vision"  # ✅ Force Spot Testnet
        FUTURES_CLIENT.FUTURES_URL = (
            "https://testnet.binancefuture.com/fapi"  # ✅ Force Futures Testnet
        )

    client = Client(api_configs.FUTURES_API_KEY, api_configs.FUTURES_API_SECRET)

    if config.USE_TESTNET:
        spot_client = SPOT_CLIENT
        futures_client = FUTURES_CLIENT
    else:
        spot_client = client
        futures_client = client

    futures_client.futures_change_leverage(symbol=symbol, leverage=config.LEVERAGE)

    logger.debug(f"[INIT] Starting bot for {symbol}")
    bot = Bot(spot_client, futures_client, symbol)
    bot.liquidate_all_positions()
    bot.run()


if __name__ == "__main__":
    mp.set_start_method("spawn")  # safer for subprocess on some OS

    processes = []

    monitor = mp.Process(target=LiveMonitor(symbol_status).run)
    monitor.start()

    for symbol in config.SYMBOLS:
        p = mp.Process(target=run_bot, args=(symbol,))
        p.start()
        processes.append(p)

    logger.debug(f"[MAIN] Running {len(processes)} bots: {', '.join(config.SYMBOLS)}")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.debug("[MAIN] Keyboard interrupt received. Terminating bots...")
        for p in processes:
            p.terminate()