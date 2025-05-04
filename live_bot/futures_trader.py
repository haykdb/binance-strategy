# futures_trader.py
from loguru import logger
from binance.exceptions import BinanceAPIException
import time


class FuturesTrader:

    def __init__(self, futures_client):
        self.futures_client = futures_client

    def safe_futures_order(
        self, symbol: str, side: str, quantity: float, max_retries=10
    ):
        attempt = 0
        original_quantity = quantity

        while attempt < max_retries:
            try:
                self.futures_client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="MARKET",
                    quantity=quantity,
                    reduceOnly=True,
                )
                logger.success(f"[ORDER SUCCESS] {side} {quantity} {symbol}")
                return True

            except BinanceAPIException as e:
                if e.code in (-4131, -1013):
                    self.futures_client.futures_order_book(symbol=symbol, limit=5)
                    logger.warning(
                        f"[WARNING] PERCENT_PRICE limit hit. Retrying with smaller size. Attempt {attempt + 1}/{max_retries}"
                    )
                    quantity = quantity / 2  # Reduce size by half
                    attempt += 1
                    time.sleep(0.1)  # Small wait before retry
                elif e.code == -2022:
                    logger.error(
                        f"[FUTURES WARNING] ReduceOnly rejected (already closed). Safe to ignore."
                    )
                    return True
                else:
                    logger.error(f"[ERROR] Order failed: {e.message}")
                    return False

        logger.error(
            f"[ERROR] Failed to place order after {max_retries} retries. Giving up."
        )
        return False

    def futures_open_long(self, symbol: str, quantity: float):
        self.futures_client.futures_create_order(
            symbol=symbol, side="BUY", type="MARKET", quantity=quantity
        )
        logger.info(f"[FUTURES] Opened LONG {quantity} {symbol}.")

    def futures_open_short(self, symbol: str, quantity: float):
        self.futures_client.futures_create_order(
            symbol=symbol, side="SELL", type="MARKET", quantity=quantity
        )
        logger.info(f"[FUTURES] Opened SHORT {quantity} {symbol}.")

    def futures_close_position(self, symbol: str, side: str, quantity: float):
        pos_info = self.futures_client.futures_position_information(symbol=symbol)
        if pos_info is None:
            return
        pos_amt = float(pos_info[0]["positionAmt"])

        if abs(pos_amt) < 1e-6:
            print(f"[FUTURES] No open futures position to close for {symbol}.")
            return

        opposite_side = "SELL" if side == "BUY" else "BUY"
        self.safe_futures_order(
            symbol=symbol, side=opposite_side, quantity=abs(pos_amt)
        )
        logger.info(f"[FUTURES] Closed {side} position {quantity} {symbol}.")


# def safe_futures_order(futures_client, symbol: str, side: str, quantity: float, max_retries=10):
#     attempt = 0
#     original_quantity = quantity
#
#     while attempt < max_retries:
#         try:
#             futures_client.futures_create_order(
#                 symbol=symbol,
#                 side=side,
#                 type='MARKET',
#                 quantity=quantity,
#                 reduceOnly=True
#             )
#             print(f"[ORDER SUCCESS] {side} {quantity} {symbol}")
#             return True
#
#         except BinanceAPIException as e:
#             if e.code == -4131:
#                 print(f"[WARNING] PERCENT_PRICE limit hit. Retrying with smaller size. Attempt {attempt+1}/{max_retries}")
#                 quantity = quantity / 2  # Reduce size by half
#                 attempt += 1
#                 time.sleep(0.1)  # Small wait before retry
#             else:
#                 print(f"[ERROR] Order failed: {e.message}")
#                 return False
#
#     print(f"[ERROR] Failed to place order after {max_retries} retries. Giving up.")
#     return False
#
# def futures_open_long(futures_client, symbol: str, quantity: float):
#     futures_client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
#     logger.info(f"[FUTURES] Opened LONG {quantity} {symbol}.")
#
# def futures_open_short(futures_client, symbol: str, quantity: float):
#     futures_client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
#     logger.info(f"[FUTURES] Opened SHORT {quantity} {symbol}.")
#
# def futures_close_position(futures_client, symbol: str, side: str, quantity: float):
#     pos_info = futures_client.futures_position_information(symbol=symbol)
#     if pos_info is None:
#         return
#     pos_amt = float(pos_info[0]['positionAmt'])
#
#     if abs(pos_amt) < 1e-6:
#         print(f"[FUTURES] No open futures position to close for {symbol}.")
#         return
#
#     opposite_side = 'SELL' if side == 'BUY' else 'BUY'
#     # futures_client.futures_create_order(
#     #     symbol=symbol,
#     #     side=opposite_side,
#     #     type='MARKET',
#     #     quantity=abs(pos_amt),
#     #     reduceOnly=True
#     # )
#     safe_futures_order(
#         futures_client=futures_client,
#         symbol=symbol,
#         side=opposite_side,
#         quantity=abs(pos_amt)
#     )
#     logger.info(f"[FUTURES] Closed {side} position {quantity} {symbol}.")
