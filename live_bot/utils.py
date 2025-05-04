# utils.py
import math


class DataLoader:

    def __init__(self, spot_client, futures_client):
        self.spot_client = spot_client
        self.futures_client = futures_client

    def get_spot_price(self, symbol: str):
        return float(self.spot_client.get_symbol_ticker(symbol=symbol)["price"])

    def get_futures_price(self, symbol: str):
        return float(self.futures_client.futures_symbol_ticker(symbol=symbol)["price"])

    def get_unrealized_pnl(self, symbol: str):
        futures_info = self.futures_client.futures_position_information(symbol=symbol)
        for p in futures_info:
            if p["symbol"] == symbol:
                return float(p["unRealizedProfit"])
        return 0.0

    def get_lot_size_filters(self, symbol: str):
        """Fetch minQty and stepSize dynamically for a symbol."""
        exchange_info = self.spot_client.get_symbol_info(symbol)
        for f in exchange_info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                min_qty = float(f["minQty"])
                step_size = float(f["stepSize"])
                return min_qty, step_size
        raise Exception(f"LOT_SIZE filter not found for symbol {symbol}")

    @staticmethod
    def adjust_quantity_to_step(quantity: float, step_size: float):
        """Adjust quantity to match Binance allowed stepSize."""
        precision = int(round(-1 * (math.log10(step_size))))
        return round(quantity, precision)

    def calculate_trade_size(self, capital_usd: float, spot_price: float, symbol: str):
        """Calculate size based on available capital and spot price."""
        min_qty, step_size = self.get_lot_size_filters(symbol)
        size = capital_usd / spot_price
        if size < min_qty:
            size = min_qty
        size = self.adjust_quantity_to_step(size, step_size)
        return size
