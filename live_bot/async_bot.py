# bot.py

import asyncio
import time
import config
from spread_model import SpreadModel
from order_manager import OrderManager
from position_manager import PositionManager
from history_logger import HistoryLogger
from loguru import logger
from margin_trader import SpotTrader


class Bot:
    def __init__(self, spot_client, futures_client, symbol, status_store=None):
        self.symbol = symbol
        self.asset = symbol.replace("USDT", "")
        self.spot = spot_client
        self.futures = futures_client

        self.order_manager = OrderManager(spot_client, futures_client)
        self.margin_trader = SpotTrader(spot_client)
        self.position_manager = PositionManager(symbol, config)
        self.logger = HistoryLogger(symbol, config)

        self.model = SpreadModel(symbol=symbol, tc=config.TC, lookback=config.STRATEGY_LOOKBACK)
        self.model_sleep = config.SPREAD_MODEL_SLEEP
        self.entry_z = config.STRATEGY_Z_ENTRY
        self.exit_z = config.STRATEGY_Z_EXIT
        self.capital = config.CAPITAL_PER_TRADE
        self.status_store = status_store

        self.last_trade_time = 0
        self.min_trade_interval = config.TRADE_SLEEP # seconds

    async def start(self):
        await asyncio.gather(
            self._model_loop(),
            self._signal_loop()
        )

    async def fetch_prices(self):
        loop = asyncio.get_event_loop()

        spot_task = loop.run_in_executor(None, lambda: self.spot.get_symbol_ticker(symbol=self.symbol))
        fut_task = loop.run_in_executor(None, lambda: self.futures.futures_mark_price(symbol=self.symbol))

        try:
            spot_data, fut_data = await asyncio.gather(spot_task, fut_task)
            spot_price = round(float(spot_data["price"]), 3)
            fut_price = round(float(fut_data["markPrice"]), 3)
            return spot_price, fut_price
        except Exception as e:
            print(f"[{self.symbol}] Price fetch error: {e}")
            return None, None

    async def _model_loop(self):
        while True:
            try:
                spot, fut = await self.fetch_prices()
                if spot and fut:
                    self.model.update(spot, fut)
                # spot = float(self.spot.get_symbol_ticker(symbol=self.symbol)["price"])
                # fut = float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"])
                # self.model.update(spot, fut)
                logger.success(f"[{self.symbol}] Model updated. {len(self.model.spread_history)}/{config.STRATEGY_LOOKBACK}")
            except Exception as e:
                logger.error(f"[{self.symbol}] Model update error: {e}")
            await asyncio.sleep(self.model_sleep)

    async def _signal_loop(self):
        while True:
            if not self.model.ready():
                await asyncio.sleep(self.model_sleep)
                continue

            try:
                spot, fut = await self.fetch_prices()
                if not spot or not fut:
                    await asyncio.sleep(0.5)
                    continue

                spread = spot - fut
                # spot = round(float(self.spot.get_symbol_ticker(symbol=self.symbol)["price"]), 4)
                # fut = round(float(self.futures.futures_mark_price(symbol=self.symbol)["markPrice"]), 4)
                # spread = spot - fut
                z = self.model.zscore(spread)
                signal = self.model.get_signal(spread)
                economic_signal = self.model.get_economic_signal(spot, fut)
                logger.info(f"[{self.symbol}] Z-score: {z:.2f}")

                # if self.position_manager.is_open:
                #     if abs(z) < self.exit_z:
                #         print(f"[{self.symbol}] Exiting position.")
                #         self.close_current_position()
                # else:
                #     now = time.time()
                #     if (now - self.last_trade_time) > self.min_trade_interval:
                #         if (z > self.entry_z) or (z < -self.entry_z and config.ALLOW_SHORT_SPREAD):
                #             self.open_position(z, spot, fut)
                #             self.last_trade_time = now

                # Respect directional constraints
                if signal == -1 and not config.ALLOW_SHORT_SPREAD:
                    logger.info(f"[STRATEGY - {self.symbol}] Short signal skipped (short spreads disabled)")
                    signal = 0

                if self.position_manager.is_open and signal == 0:
                    logger.debug(f"[ACTION - {self.symbol}] Closing open position due to neutral signal.")
                    self.close_current_position()

                if not self.position_manager.is_open and signal in (1, -1) and economic_signal:
                    now = time.time()
                    if (now - self.last_trade_time) > self.min_trade_interval:
                        logger.debug(f"[ACTION - {self.symbol}] Opening new position.")
                        self.open_position(signal, spot, fut)
                        self.last_trade_time = now
                await asyncio.sleep(self.min_trade_interval)
                continue

            except Exception as e:
                print(f"[{self.symbol}] Signal loop error: {e}")
                continue
            # await asyncio.sleep(0.5)

    def open_position(self, direction: int, spot_price: float, futures_price: float):
        try:
            qty = round(config.CAPITAL_PER_TRADE / futures_price, 3)
            side = 'LONG' if direction > 0 else 'SHORT'

            spot_success = (
                self.order_manager.spot_buy(self.symbol, qty)
                if side == 'LONG' else
                self.margin_trader.margin_sell(self.asset, qty)  # self.order_manager.spot_sell(self.symbol, qty)
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


