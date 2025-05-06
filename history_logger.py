# history_logger.py

import csv
import os
from datetime import date

COLUMNS = [
    "Action",
    "Side",
    "Symbol",
    "Size",
    "Spot Entry Price",
    "Spot Exit Price",
    "Futures Entry Price",
    "Futures Exit Price",
    "Entry Time",
    "Exit Time",
    "Spot PnL (USD)",
    "Futures PnL (USD)",
    "Total Net PnL (USD)",
    "Holding Duration (minutes)",
]


class HistoryLogger:

    def __init__(self, symbol, config):
        self.symbol = symbol
        self.config = config

    def log_event(self, event_data: dict):
        path = os.path.abspath(self.config.TRADE_LOG_PATH.format(symbol=self.symbol, t=date.today()))
        file_exists = os.path.exists(path)

        if not os.path.exists(path):
            with open(path, "a", newline="") as csvfile:
                pass

        with open(path, "a", newline="") as csvfile:
            fieldnames = list(event_data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)

            if not file_exists:
                writer.writeheader()

            writer.writerow(event_data)

    @staticmethod
    def format_trade_event(
        timestamp,
        action,
        position_side,
        spot_price,
        futures_price,
        quantity,
        extra_info=None,
    ):
        event = {
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Action": action,  # 'OPEN' or 'CLOSE'
            "Position Side": position_side,  # 'LONG' or 'SHORT'
            "Spot Price": round(spot_price, 2),
            "Futures Price": round(futures_price, 2),
            "Quantity": quantity,
        }
        if extra_info:
            event.update(extra_info)
        return event


# def log_event(event_data: dict):
#     file_exists = os.path.isfile(HISTORY_FILE)
#
#     with open(HISTORY_FILE, 'a', newline='') as csvfile:
#         fieldnames = list(event_data.keys())
#         writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
#
#         if not file_exists:
#             writer.writeheader()
#
#         writer.writerow(event_data)
#
# def format_trade_event(timestamp, action, position_side, spot_price, futures_price, quantity, extra_info=None):
#     event = {
#         'Timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
#         'Action': action,  # 'OPEN' or 'CLOSE'
#         'Position Side': position_side,  # 'LONG' or 'SHORT'
#         'Spot Price': round(spot_price, 2),
#         'Futures Price': round(futures_price, 2),
#         'Quantity': quantity
#     }
#     if extra_info:
#         event.update(extra_info)
#     return event
