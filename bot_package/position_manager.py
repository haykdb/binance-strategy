# position_manager.py
#
# from datetime import datetime
#
#
# class PositionManager:
#     def __init__(self):
#         self.reset()
#
#     def open(self, side: str, spot_price: float, futures_price: float, size: float):
#         """Open a new position."""
#         if self.is_open:
#             raise Exception("Position already open! Cannot open a new position without closing the existing one.")
#
#         self.side = side  # 'LONG' or 'SHORT'
#         self.spot_entry_price = spot_price
#         self.futures_entry_price = futures_price
#         self.size = size
#         self.entry_time = datetime.utcnow()
#         self.is_open = True
#
#     def close(self, spot_exit_price: float, futures_exit_price: float) -> dict:
#         """Close the current position and calculate PnL."""
#         if not self.is_open:
#             raise Exception("No open position to close!")
#
#         exit_time = datetime.utcnow()
#
#         # Spot PnL calculation
#         if self.side == 'LONG':
#             spot_pnl = (spot_exit_price - self.spot_entry_price) * self.size
#             futures_pnl = (self.futures_entry_price - futures_exit_price) * self.size
#         elif self.side == 'SHORT':
#             spot_pnl = (self.spot_entry_price - spot_exit_price) * self.size
#             futures_pnl = (futures_exit_price - self.futures_entry_price) * self.size
#         else:
#             raise Exception("Invalid side in PositionManager.")
#
#         # Estimate total fees (open + close fees)
#         estimated_fee_rate = 0.0004  # Futures taker fee (0.04%)
#         total_trade_notional = (
#                                            self.spot_entry_price + spot_exit_price + self.futures_entry_price + futures_exit_price) * self.size
#         estimated_fees = total_trade_notional * estimated_fee_rate
#
#         total_net_pnl = spot_pnl + futures_pnl - estimated_fees
#
#         holding_minutes = round((exit_time - self.entry_time).total_seconds() / 60, 2)
#
#         result = {
#             'Side': self.side,
#             'Entry Time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
#             'Exit Time': exit_time.strftime("%Y-%m-%d %H:%M:%S"),
#             'Spot Entry Price': round(self.spot_entry_price, 2),
#             'Spot Exit Price': round(spot_exit_price, 2),
#             'Futures Entry Price': round(self.futures_entry_price, 2),
#             'Futures Exit Price': round(futures_exit_price, 2),
#             'Size': self.size,
#             'Spot PnL (USD)': round(spot_pnl, 2),
#             'Futures PnL (USD)': round(futures_pnl, 2),
#             'Total Net PnL (USD)': round(total_net_pnl, 2),
#             'Holding Duration (minutes)': holding_minutes
#         }
#
#         self.reset()
#         return result
#
#     def reset(self):
#         """Reset the position state."""
#         self.side = None
#         self.spot_entry_price = 0
#         self.futures_entry_price = 0
#         self.size = 0
#         self.entry_time = None
#         self.is_open = False


# position_manager.py

from datetime import datetime, timezone
from loguru import logger


class PositionManager:
    def __init__(self, symbol, config):
        self.config = config
        self.symbol = symbol
        self.reset()

    def open(self, side: str, spot_price: float, futures_price: float, size: float):
        if self.is_open:
            raise Exception(
                "Position already open. Must close before opening a new one."
            )

        self.side = side  # 'LONG' or 'SHORT'
        self.spot_entry_price = spot_price
        self.futures_entry_price = futures_price
        self.size = size
        self.entry_time = datetime.now(tz=timezone.utc)
        self.is_open = True

    def close(self, spot_exit_price: float, futures_exit_price: float) -> dict:
        if not self.is_open:
            raise Exception("No open position to close.")

        exit_time = datetime.now(tz=timezone.utc)

        # Spot and Futures PnL
        if self.side == "LONG":
            spot_pnl = (spot_exit_price - self.spot_entry_price) * self.size
            futures_pnl = (self.futures_entry_price - futures_exit_price) * self.size
        elif self.side == "SHORT":
            spot_pnl = (self.spot_entry_price - spot_exit_price) * self.size
            futures_pnl = (futures_exit_price - self.futures_entry_price) * self.size
        else:
            raise Exception("Invalid side.")

        estimated_fee_rate = self.config.TC  # Total fee estimate (entry + exit)
        notional = (
            self.spot_entry_price
            + spot_exit_price
            + self.futures_entry_price
            + futures_exit_price
        ) * self.size
        fees = estimated_fee_rate * notional
        total_net_pnl = spot_pnl + futures_pnl - fees

        holding_minutes = round((exit_time - self.entry_time).total_seconds() / 60, 2)

        result = {
            "Action": "CLOSE",
            "Side": self.side,
            "Symbol": self.symbol,
            "Size": round(self.size, 6),
            "Spot Entry Price": round(self.spot_entry_price, 2),
            "Spot Exit Price": round(spot_exit_price, 2),
            "Futures Entry Price": round(self.futures_entry_price, 2),
            "Futures Exit Price": round(futures_exit_price, 2),
            "Entry Time": self.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Spot PnL (USD)": round(spot_pnl, 2),
            "Futures PnL (USD)": round(futures_pnl, 2),
            "Total Net PnL (USD)": round(total_net_pnl, 2),
            "Holding Duration (minutes)": holding_minutes,
        }

        self.reset()
        return result

    def position_info(self):
        if self.is_open:
            return f"[POSITION]: {self.side} Spread, Spot Entry: {self.spot_entry_price}, Futures Entry: {self.futures_entry_price}."
        else:
            return "No OPEN Positions at the moment."

    def calc_closing_spot_pnl(self, exit_spot_price: float) -> float:
        if not self.is_open:
            logger.warning(
                f"Trying to calculate spot closing pnl when position is closed."
            )
            return 0.0
        if self.side == "LONG":
            spot_pnl = (exit_spot_price - self.spot_entry_price) * self.size
        else:
            spot_pnl = (self.spot_entry_price - exit_spot_price) * self.size
        return spot_pnl

    def calc_closing_futures_pnl(self, exit_futures_price: float) -> float:
        if not self.is_open:
            logger.warning(
                f"Trying to calculate futures closing pnl when position is closed."
            )
            return 0.0
        if self.side == "LONG":
            futures_pnl = (self.futures_entry_price - exit_futures_price) * self.size
        else:
            futures_pnl = (exit_futures_price - self.futures_entry_price) * self.size
        return futures_pnl

    def calc_total_pnl(
        self, exit_spot_price: float, exit_futures_price: float
    ) -> float:
        spot_pnl = self.calc_closing_spot_pnl(exit_spot_price)
        futures_pnl = self.calc_closing_futures_pnl(exit_futures_price)
        return spot_pnl + futures_pnl

    def get_futures_entry_side(self):
        assert self.is_open
        if self.side == "LONG":
            return "SELL"
        else:
            return "BUY"

    def reset(self):
        self.side = None
        self.spot_entry_price = 0
        self.futures_entry_price = 0
        self.size = 0
        self.entry_time = None
        self.is_open = False

    def get_futures_position_size(self, futures_client, symbol: str):
        info = futures_client.futures_position_information(symbol=symbol)
        return float(info[0]["positionAmt"])

    def get_spot_balance(self, spot_client, asset: str):
        account = spot_client.get_account()
        for balance in account["balances"]:
            if balance["asset"] == asset:
                return float(balance["free"]) + float(balance["locked"])
        return 0.0

    def get_margin_position(self, spot_client, asset: str):
        account = spot_client.get_margin_account()
        for item in account["userAssets"]:
            if item["asset"] == asset:
                borrowed = float(item["borrowed"])
                net_position = float(item["free"]) - borrowed
                return {"borrowed": borrowed, "net_position": net_position}
        return {"borrowed": 0.0, "net_position": 0.0}

    def check_all_positions_closed(
        self, spot_client, futures_client, symbol: str, asset: str
    ) -> bool:
        fut_size = abs(self.get_futures_position_size(futures_client, symbol))
        spot_balance = self.get_spot_balance(spot_client, asset)
        margin = self.get_margin_position(spot_client, asset)
        borrowed = margin["borrowed"]

        print(
            f"[CHECK] Futures: {fut_size:.6f}, Spot: {spot_balance:.6f}, Margin Borrowed: {borrowed:.6f}"
        )

        return fut_size < 1e-6 and spot_balance < 1e-6 and borrowed < 1e-6

    def get_total_notional(self, spot_price: float, futures_price: float) -> float:
        if not self.is_open:
            return 0.0
        return self.size * (spot_price + futures_price)
