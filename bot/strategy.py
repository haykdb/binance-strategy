# strategy.py

import numpy as np
from typing import Union


class StrategyCalculator:

    def __init__(self, configs):
        self.configs = configs
        self.spread_history = []

    def update_spread(self, spot: float, futures: float) -> float:
        spread = spot - futures
        self.spread_history.append(spread)
        if len(self.spread_history) > self.configs.LOOKBACK:
            del self.spread_history[0]
        return spread

    def calculate_zscore(self) -> Union[float, None]:
        if len(self.spread_history) < self.configs.LOOKBACK:
            return None
        mean = np.mean(self.spread_history)
        std = np.std(self.spread_history)
        if std == 0:
            return None
        return (self.spread_history[-1] - mean) / std

    def calculate_expected_tc(self, spot: float, futures: float) -> float:
        return 2 * (spot * self.configs.TC + futures * self.configs.TC)

    def calculate_expected_profit(self):
        mean = np.mean(self.spread_history)
        return abs(self.spread_history[-1] - mean)

# def update_spread(spot: float, futures: float):
#     spread = spot - futures
#     spread_history.append(spread)
#     if len(spread_history) > config.LOOKBACK:
#         del spread_history[0]
#     return spread

# def calculate_zscore():
#     if len(spread_history) < config.LOOKBACK:
#         return None
#     mean = np.mean(spread_history)
#     std = np.std(spread_history)
#     if std == 0:
#         return None
#     return (spread_history[-1] - mean) / std

# def calculate_expected_tc(spot: float, futures: float) -> float:
#     return 2 * (spot * TC + futures * TC)
#
# def calculate_expected_profit():
#     mean = np.mean(spread_history)
#     return abs(spread_history[-1] - mean)
