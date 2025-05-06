# main.py

import multiprocessing as mp
import config
from async_bot import Bot
from binance.client import Client
from loguru import logger
from datetime import date

LOGGER = f"/Users/admin/PycharmProjects/binance-strategy/logs/{date.today()}.log"
logger.add(LOGGER)

# === CONNECT ===
LIVE_CLIENT = Client(
    config.API_KEY, config.API_SECRET, testnet=config.USE_TESTNET
)
SPOT_CLIENT = Client(
    config.SPOT_API_KEY, config.SPOT_API_SECRET, testnet=config.USE_TESTNET
)
FUTURES_CLIENT = Client(
    config.FUTURES_API_KEY, config.FUTURES_API_SECRET, testnet=config.USE_TESTNET
)


def run_bot(symbol):
    import asyncio  # must be imported here for multiprocessing on macOS

    # === MANUALLY SET TESTNET URLs ===
    if config.USE_TESTNET:
        SPOT_CLIENT.API_URL = "https://testnet.binance.vision"  # ✅ Force Spot Testnet
        FUTURES_CLIENT.FUTURES_URL = (
            "https://testnet.binancefuture.com/fapi"  # ✅ Force Futures Testnet
        )

    if config.USE_TESTNET:
        spot_client = SPOT_CLIENT
        futures_client = FUTURES_CLIENT
    else:
        spot_client = LIVE_CLIENT
        futures_client = LIVE_CLIENT

    logger.debug(f"[INIT] Starting bot for {symbol}")
    bot = Bot(spot_client, futures_client, symbol)
    bot.liquidate_all_positions()
    asyncio.run(bot.start())


if __name__ == "__main__":
    mp.set_start_method("spawn")

    processes = []

    for symbol in config.SYMBOLS:
        p = mp.Process(target=run_bot, args=(symbol,))
        p.start()
        processes.append(p)

    logger.debug(f"[MAIN] Running {len(processes)} bots: {', '.join(config.SYMBOLS)}")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.error("[MAIN] Gracefully shutting down...")
        for p in processes:
            p.terminate()
