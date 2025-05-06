# strategy.py

import pandas as pd
import numpy as np
from loguru import logger
import live_bot.config as config


class Strategy:
    def __init__(self, symbol):
        self.lookback = config.STRATEGY_LOOKBACK
        self.entry_z = config.STRATEGY_Z_ENTRY
        self.exit_z = config.STRATEGY_Z_EXIT
        self.symbol = symbol
        self.TC = config.TC
        self.allow_short = config.ALLOW_SHORT_SPREAD
        self.history = pd.DataFrame(columns=["timestamp", "spot", "futures"])
        self.entry_signal_m1 = None

    def update(self, timestamp, spot_price, futures_price):
        self.history.loc[timestamp] = [timestamp, spot_price, futures_price]
        self.history = self.history.tail(self.lookback + 5)

    def calc_z_score(self) -> float:
        df = self.history.copy()
        df["spread"] = df["spot"] - df["futures"]
        mean = df["spread"].rolling(self.lookback).mean().iloc[-1]
        std = df["spread"].rolling(self.lookback).std().iloc[-1]

        if std == 0:
            return 0

        z = (df["spread"].iloc[-1] - mean) / std
        return z

    def get_signal(self) -> int:
        if len(self.history) < self.lookback:
            logger.info(f"Building history {self.symbol} {len(self.history)}/{self.lookback}...")
            return 0
        z = self.calc_z_score()
        logger.info(f"[STRATEGY] {self.symbol} Z-score: {round(z, 2)}")

        if not self.entry_signal_m1 is None:
            if self.entry_signal_m1 == 1 and z >= self.exit_z:
                return 0
            elif self.entry_signal_m1 == -1 and z <= -self.exit_z:
                return 0

        if abs(z) < self.exit_z:
            return 0
        elif z > self.entry_z and self.allow_short:
            self.entry_signal_m1 = -1
            return -1
        elif z < -self.entry_z:
            self.entry_signal_m1 = 1
            return 1
        return 2

    def calculate_expected_tc(self, spot: float, futures: float) -> float:
        return 2 * (spot * self.TC + futures * self.TC)

    def calculate_expected_profit(self) -> float:
        if len(self.history) < self.lookback:
            return 0.0

        df = self.history.copy()
        df["spread"] = df["spot"] - df["futures"]
        mean = df["spread"].rolling(self.lookback).mean().iloc[-1]
        return abs(float(df["spread"].iloc[-1]) - mean)

    def get_economic_signal(self) -> bool:
        df = self.history.copy()
        spot = float(df["spot"].iloc[-1])
        futures = float(df["futures"].iloc[-1])
        return bool(self.calculate_expected_profit() > self.calculate_expected_tc(spot, futures))
