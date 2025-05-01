import os
import time
from pathlib import Path
from loguru import logger

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

SPOT_BASE_URL = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"
SPOT_ENDPOINT = "/api/v3/klines"
FUTURES_ENDPOINT = "/fapi/v1/klines"

# Configuration
# SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "XRPUSDT", "DOTUSDT", "ATOMUSDT"]

INTERVAL = "1m"
LIMIT = 1000  # max per request
DAYS = 20
SLEEP_SECONDS = 0.2  # adjust for rate limits


def ms(dt):
    return int(dt.timestamp() * 1000)


def fetch_klines(symbol, start_time, end_time, is_futures):
    url = f"{FUTURES_BASE_URL if is_futures else SPOT_BASE_URL}{FUTURES_ENDPOINT if is_futures else SPOT_ENDPOINT}"
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": LIMIT,
        "startTime": start_time,
        "endTime": end_time,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if isinstance(data, dict) and "code" in data:
        print(f"Error fetching {symbol}: {data}")
        return None

    df = pd.DataFrame(
        data,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_volume",
            "taker_buy_quote_volume",
            "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df.astype(float)


def download_symbol(symbol, is_futures):
    print(f"\n[+] Downloading {'Futures' if is_futures else 'Spot'} data for {symbol}")
    now = datetime.now(tz=timezone.utc)
    start = now - timedelta(days=DAYS)

    all_data = []

    current = start
    end = now

    while current < end:
        start_ms = ms(current)
        next_chunk = current + timedelta(minutes=LIMIT)
        end_ms = ms(next_chunk)

        df = fetch_klines(symbol, start_ms, end_ms, is_futures)
        if df is not None and not df.empty:
            all_data.append(df)
        else:
            print(f"[!] Empty response for {symbol} at {current}")

        current = next_chunk
        time.sleep(SLEEP_SECONDS)

    if all_data:
        result = pd.concat(all_data)
        result = result[~result.index.duplicated(keep="first")]
        filename = f"{symbol}_{'futures' if is_futures else 'spot'}.csv"
        result.to_csv(Path("/Users/admin/PycharmProjects/BinanceBot/data") / filename)
        print(f"[✔] Saved {filename} with {len(result)} rows")
    else:
        print(f"[x] No data for {symbol}")


def get_all_coins():
    URL = "https://scalpscreener.com/api/contracts"
    resp = requests.get(URL)
    coins = {}
    for contract in list(resp.json()):
        ticker = contract["pair"]
        id = contract["id"]
        coins[ticker] = id
    return list(coins.keys())


if __name__ == "__main__":
    symbols = get_all_coins()[310:]
    i = 1
    for symbol in symbols:
        download_symbol(symbol, is_futures=True)  # spot
        download_symbol(symbol, is_futures=False)  # perp
        logger.success(
            f"{symbol} is succesfully downloaded, {i}/{len(symbols)} completed..."
        )
        i += 1
