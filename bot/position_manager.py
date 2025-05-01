# position_manager.py

from datetime import datetime


class PositionManager:
    def __init__(self):
        self.reset()

    def open(self, side: str, spot_price: float, futures_price: float, size: float):
        """Open a new position."""
        if self.is_open:
            raise Exception("Position already open! Cannot open a new position without closing the existing one.")

        self.side = side  # 'LONG' or 'SHORT'
        self.spot_entry_price = spot_price
        self.futures_entry_price = futures_price
        self.size = size
        self.entry_time = datetime.utcnow()
        self.is_open = True

    def close(self, spot_exit_price: float, futures_exit_price: float) -> dict:
        """Close the current position and calculate PnL."""
        if not self.is_open:
            raise Exception("No open position to close!")

        exit_time = datetime.utcnow()

        # Spot PnL calculation
        if self.side == 'LONG':
            spot_pnl = (spot_exit_price - self.spot_entry_price) * self.size
            futures_pnl = (self.futures_entry_price - futures_exit_price) * self.size
        elif self.side == 'SHORT':
            spot_pnl = (self.spot_entry_price - spot_exit_price) * self.size
            futures_pnl = (futures_exit_price - self.futures_entry_price) * self.size
        else:
            raise Exception("Invalid side in PositionManager.")

        # Estimate total fees (open + close fees)
        estimated_fee_rate = 0.0004  # Futures taker fee (0.04%)
        total_trade_notional = (
                                           self.spot_entry_price + spot_exit_price + self.futures_entry_price + futures_exit_price) * self.size
        estimated_fees = total_trade_notional * estimated_fee_rate

        total_net_pnl = spot_pnl + futures_pnl - estimated_fees

        holding_minutes = round((exit_time - self.entry_time).total_seconds() / 60, 2)

        result = {
            'Side': self.side,
            'Entry Time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            'Exit Time': exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            'Spot Entry Price': round(self.spot_entry_price, 2),
            'Spot Exit Price': round(spot_exit_price, 2),
            'Futures Entry Price': round(self.futures_entry_price, 2),
            'Futures Exit Price': round(futures_exit_price, 2),
            'Size': self.size,
            'Spot PnL (USD)': round(spot_pnl, 2),
            'Futures PnL (USD)': round(futures_pnl, 2),
            'Total Net PnL (USD)': round(total_net_pnl, 2),
            'Holding Duration (minutes)': holding_minutes
        }

        self.reset()
        return result

    def reset(self):
        """Reset the position state."""
        self.side = None
        self.spot_entry_price = 0
        self.futures_entry_price = 0
        self.size = 0
        self.entry_time = None
        self.is_open = False
