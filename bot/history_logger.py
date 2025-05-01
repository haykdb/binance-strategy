# history_logger.py

import csv
import os

COLUMNS = [
    'Timestamp',
    'Action',  # 'OPEN' or 'CLOSE'
    'Position Side',  # 'LONG' or 'SHORT'
    'Spot Price',
    'Futures Price',
    'Quantity',
    'Expected TC',
    'Expected Profit',
    'Spot PnL (USD)',
    'Futures PnL (USD)',
    'Total Net PnL (USD)',
    'Cumulative Pnl',
]

class HistoryLogger:

    def __init__(self, config):
        self.config = config

    def log_event(self, event_data: dict):
        path = self.config.HISTORY_FILE.format(symbol=self.config.SYMBOL)
        file_exists = os.path.isfile(path)

        with open(path, 'a', newline='') as csvfile:
            fieldnames = list(event_data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)

            if not file_exists:
                writer.writeheader()

            writer.writerow(event_data)

    @staticmethod
    def format_trade_event(timestamp, action, position_side, spot_price, futures_price, quantity, extra_info=None):
        event = {
            'Timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'Action': action,  # 'OPEN' or 'CLOSE'
            'Position Side': position_side,  # 'LONG' or 'SHORT'
            'Spot Price': round(spot_price, 2),
            'Futures Price': round(futures_price, 2),
            'Quantity': quantity
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
