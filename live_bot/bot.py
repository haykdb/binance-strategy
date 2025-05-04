import time
from loguru import logger
import live_bot.config as config
from live_bot.strategy import Strategy
from live_bot.order_manager import OrderManager
from live_bot.position_manager import PositionManager
from live_bot.history_logger import HistoryLogger
from live_bot.margin_trader import SpotTrader
from datetime import date

LOGGER = "/Users/admin/PycharmProjects/binance-strategy/logs/{t:%Y-%m-%d}_{symbol}.log"

# TODO currently spot shorting is not fully implemented since it requires Margin Trading and has no testnet. TBI
class Bot: # Todo adjust fields in history logger for better naming and structure
    def __init__(self, spot_client, futures_client, symbol):
        self.symbol = symbol
        self.asset = self.symbol.replace("USDT", "")
        self.capital = config.CAPITAL_PER_TRADE

        self.order_manager = OrderManager(spot_client, futures_client)
        self.margin_trader = SpotTrader(spot_client)

        self.position_manager = PositionManager(self.symbol, config)
        self.strategy = Strategy(self.symbol)
        self.logger = HistoryLogger(self.symbol, config)

        self.spot = spot_client
        self.futures = futures_client

        logger.add(LOGGER.format(t=date.today(), symbol=self.symbol))


    def run(self):
        while True:
            self.step()
            time.sleep(config.STRATEGY_SLEEP)

    def step(self):
        try:
            spot_price = round(float(self.spot.get_symbol_ticker(symbol=self.symbol)["price"]), 4)
            futures_price = round(float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"]), 4)

            self.strategy.update(timestamp=time.time(), spot_price=spot_price, futures_price=futures_price)
            signal = self.strategy.get_signal()
            economic_signal = self.strategy.get_economic_signal()

            # Respect directional constraints
            if signal == -1 and not config.ALLOW_SHORT_SPREAD:
                logger.info(f"[STRATEGY - {self.symbol}] Short signal skipped (short spreads disabled)")
                signal = 0

            if self.position_manager.is_open and signal == 0:
                logger.debug(f"[ACTION - {self.symbol}] Closing open position due to neutral signal.")
                self.close_current_position()
                return

            if not self.position_manager.is_open and signal in (1, -1) and economic_signal:
                logger.debug(f"[ACTION - {self.symbol}] Opening new position.")
                self.open_position(signal, spot_price, futures_price)
                return

        except Exception as e:
            logger.error(f"[ERROR - {self.symbol}] Step failed: {e}")
            logger.warning("Closing all open positions.")
            self.liquidate_all_positions()

    def open_position(self, direction: int, spot_price: float, futures_price: float):
        try:
            qty = round(config.CAPITAL_PER_TRADE / futures_price, 3)
            side = 'LONG' if direction > 0 else 'SHORT'

            spot_success = (
                self.order_manager.spot_buy(self.symbol, qty)
                if side == 'LONG' else
                self.margin_trader.margin_sell(self.asset, qty) # self.order_manager.spot_sell(self.symbol, qty)
            )

            fut_success = (
                self.order_manager.futures_sell(self.symbol, qty)
                if side == 'LONG' else
                self.order_manager.futures_buy(self.symbol, qty)
            )

            if spot_success and fut_success:
                self.position_manager.open(side, spot_price=futures_price, futures_price=futures_price, size=qty)
                self.logger.log_event({
                    'Action': 'OPEN',
                    'Side': side,
                    'Symbol': self.symbol,
                    'Size': qty,
                    'Futures Entry Price': futures_price,
                    'Spot Entry Price': spot_price
                })
            else:
                self.liquidate_all_positions()
                logger.error(f"[ERROR - {self.symbol}] Order failed. Closed all open positions.")


        except Exception as e:
            self.liquidate_all_positions()
            logger.error(f"[ERROR - {self.symbol}] Failed to open position: {e}. "
                         f"Closed all open positions.")

    def close_current_position(self):
        try:
            qty = self.position_manager.size
            spot_closed = self.order_manager.close_spot_position(self.symbol)
            futures_closed = self.order_manager.close_futures_position(self.symbol)

            if spot_closed and futures_closed:
                spot_price = float(self.spot.get_symbol_ticker(symbol=self.symbol)["price"])
                futures_price = float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"])
                result = self.position_manager.close(spot_price, futures_price)
                self.logger.log_event({
                    'Action': 'CLOSE',
                    **result
                })
            else:
                self.liquidate_all_positions()
                logger.error(f"[ERROR - {self.symbol}] Failed to close both legs. Closed all open positions.")

        except Exception as e:
            self.liquidate_all_positions()
            logger.error(f"[ERROR - {self.symbol}] Close failed: {e}. Closed all open positions.")

    def liquidate_all_positions(self):
        liquidate_spot = False
        liquidate_futures = False
        while not (liquidate_spot and liquidate_futures):
            liquidate_spot = self.order_manager.close_position(self.symbol, False)
            liquidate_futures = self.order_manager.close_position(self.symbol, True)






# class Bot:
#     def __init__(self, spot_client, futures_client, symbol: str):
#         self.symbol = symbol
#         self.asset = symbol.replace("USDT", "")
#         self.order_manager = OrderManager(spot_client, futures_client)
#         self.position_manager = PositionManager()
#         self.logger = HistoryLogger("data/trades.csv")
#         self.spot = spot_client
#         self.futures = futures_client
#
#     def run(self):
#         """Main trading loop."""
#         while True:
#             self.step()
#             time.sleep(60)  # Adjustable based on strategy
#
#     def step(self):
#         """Performs one cycle of market logic."""
#         try:
#             # 1. Get mid-price and spread
#             mark_price = float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"])
#             depth = self.futures.futures_order_book(symbol=self.symbol, limit=5)
#             best_bid = float(depth['bids'][0][0])
#             best_ask = float(depth['asks'][0][0])
#             mid_price = (best_bid + best_ask) / 2
#             spread = best_ask - best_bid
#
#             # 2. Skip wide spreads
#             if spread / mid_price > 0.02:
#                 print("[SPREAD] Too wide — skipping this cycle.")
#                 return
#
#             # 3. Get trade signal
#             signal = self.generate_signal()
#             print(f"[SIGNAL] Signal = {signal}")
#
#             # 4. Exit logic
#             if self.position_manager.is_open and signal == 0:
#                 print("[ACTION] Closing open position due to neutral signal.")
#                 self.close_current_position()
#                 return
#
#             # 5. Entry logic
#             if not self.position_manager.is_open and signal != 0:
#                 print("[ACTION] Opening new position.")
#                 self.open_position(signal)
#                 return
#
#         except Exception as e:
#             print(f"[ERROR] Step error: {e}")
#
#     def open_position(self, direction: int):
#         """Opens a new spread position: LONG = long spot, short futures."""
#         try:
#             futures_price = float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"])
#             qty = round(1000 / futures_price, 6)
#             side = 'LONG' if direction > 0 else 'SHORT'
#
#             # Spot order
#             spot_success = (
#                 self.order_manager.spot_buy(self.symbol, qty)
#                 if side == 'LONG' else
#                 self.order_manager.spot_sell(self.symbol, qty)
#             )
#
#             # Futures order
#             fut_success = (
#                 self.order_manager.futures_sell(self.symbol, qty)
#                 if side == 'LONG' else
#                 self.order_manager.futures_buy(self.symbol, qty)
#             )
#
#             if spot_success and fut_success:
#                 self.position_manager.open(side, spot_price=futures_price, futures_price=futures_price, size=qty)
#                 self.logger.log_event({
#                     'Action': 'OPEN',
#                     'Side': side,
#                     'Symbol': self.symbol,
#                     'Size': qty,
#                     'Price': futures_price
#                 })
#             else:
#                 print("[ERROR] Failed to open both legs. Consider rollback.")
#
#         except Exception as e:
#             print(f"[ERROR] Failed to open position: {e}")
#
#     def close_current_position(self):
#         """Closes both legs and logs result."""
#         try:
#             side = self.position_manager.side
#             qty = self.position_manager.size
#
#             spot_closed = self.order_manager.close_spot_position(self.symbol)
#             futures_closed = self.order_manager.close_futures_position(self.symbol)
#
#             if spot_closed and futures_closed:
#                 spot_price = float(self.spot.get_symbol_ticker(symbol=self.symbol)["price"])
#                 futures_price = float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"])
#                 result = self.position_manager.close(spot_price, futures_price)
#                 self.logger.log_event({
#                     'Action': 'CLOSE',
#                     **result
#                 })
#             else:
#                 print("[ERROR] One or both legs failed to close.")
#
#         except Exception as e:
#             print(f"[ERROR] Failed to close position: {e}")
#
#     def generate_signal(self) -> int:
#         """
#         Stub for your strategy.
#         Returns:
#             +1 = enter long
#             -1 = enter short
#              0 = do nothing
#         """
#         # Replace this with your real signal logic
#         return 0
#

#