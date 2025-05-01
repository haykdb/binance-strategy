import requests
import pandas as pd
import time
import os
from datetime import datetime

BASE_URL = "https://api.binance.com"


def fetch_klines(
    symbol, interval="1s", limit=1000, start_time=None, end_time=None, is_futures=False
):
    endpoint = "/fapi/v1/klines" if is_futures else "/api/v3/klines"
    url = f"{BASE_URL}{endpoint}"

    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time

    response = requests.get(url, params=params)
    data = response.json()

    if isinstance(data, dict) and "code" in data:
        raise Exception(f"Error fetching data: {data['msg']}")

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


# Example usage
if __name__ == "__main__":
    symbol = "BTCUSDT"
    interval = "1s"
    is_futures = False  # True for perpetuals

    now = int(time.time() * 1000)
    one_hour = 60 * 60 * 1000
    start = now - one_hour  # 1 hour back

    df = fetch_klines(
        symbol, interval=interval, start_time=start, is_futures=is_futures
    )
    filename = f"{symbol}_{'futures' if is_futures else 'spot'}_{interval}.csv"
    df.to_csv(filename)
    print(f"Saved {filename}, {len(df)} rows.")
