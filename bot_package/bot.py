# bot.py

from loguru import logger
import time
import config
from margin_trader import SpotTrader
from futures_trader import FuturesTrader  # import futures_trader as futures
from strategy import StrategyCalculator  # import strategy
from utils import DataLoader  # import utils
from binance.client import Client
from history_logger import HistoryLogger  # import history_logger
from datetime import datetime, timezone, date
from position_manager import PositionManager
from order_manager import OrderManager
from final_bot import Bot

LOGGER = f"/Users/admin/PycharmProjects/binance-strategy/logs/{date.today()}.log"
logger.add(LOGGER)

# TODO Add Transaction Costs ✅
# TODO Make better live pnl tracking ✅
# TODO Add Trade Class to record all trades, monitor all positions, keep in history ✅
# TODO Add Position Management, Close and Liquidate if positions get too big or too small or: Check before opening a trade that position is already open or not ✅
# TODO Make Position Manager More Robust
# Todo Integrate Position Manager in the bot
# TODO Divide Bot into different code sections
# TODO Trader Order Manager Should be able to handle ALL Open/Close orders for API errors
# TODO When enter
# TODO Add logic to close all positions if something is wrong

# === CONNECT ===
spot_client = Client(
    config.SPOT_API_KEY, config.SPOT_API_SECRET, testnet=config.USE_TESTNET
)
futures_client = Client(
    config.FUTURES_API_KEY, config.FUTURES_API_SECRET, testnet=config.USE_TESTNET
)

# === MANUALLY SET TESTNET URLs ===
if config.USE_TESTNET:
    spot_client.API_URL = "https://testnet.binance.vision"  # ✅ Force Spot Testnet
    futures_client.FUTURES_URL = (
        "https://testnet.binancefuture.com/fapi"  # ✅ Force Futures Testnet
    )

futures_client.futures_change_leverage(symbol=config.SYMBOL, leverage=config.LEVERAGE)

bot = Bot(spot_client, futures_client)
bot.run()
#
# # === INITIATING ALL CLASSES ===
# trader_spot = SpotTrader(spot_client=spot_client)
# trader_futures = FuturesTrader(futures_client=futures_client)
# strategy = StrategyCalculator(configs=config)
# dataloader = DataLoader(spot_client=spot_client, futures_client=futures_client)
# historymanager = HistoryLogger(config=config)
# positionmanager = PositionManager()
# ordermanager = OrderManager(spot_client=spot_client, futures_client=futures_client)
#
#
# # === STATE ===
# cumulative_pnl = 0.0
#
# logger.info("[BOT] Starting...")
#
# while True:
#     try:
#         spot_price = round(dataloader.get_spot_price(config.SYMBOL), 4)
#         futures_price = round(dataloader.get_futures_price(config.SYMBOL), 4)
#         spread = strategy.update_spread(spot_price, futures_price)
#         zscore = strategy.calculate_zscore()
#
#         exp_profit = strategy.calculate_expected_profit()
#         exp_tc = 0  # strategy.calculate_expected_tc(spot_price, futures_price)
#
#         if zscore is None:
#             logger.info(
#                 f"Building history ({len(strategy.spread_history)}/{config.LOOKBACK})..."
#             )
#             time.sleep(config.SLEEP_TIME)
#             continue
#
#         size = round(
#             dataloader.calculate_trade_size(
#                 config.CAPITAL_PER_TRADE, spot_price, config.SYMBOL
#             ),
#             1,
#         )
#
#         logger.info(
#             f"[SPREAD] Spot: {spot_price:.4f}, Futures: {futures_price:.4f}, Spread: {spread:.4f}, Z: {zscore:.2f}, TC: {exp_tc}, PF: {exp_profit}"
#         )
#
#         # STOP-LOSS CHECK
#         # if position != 0:
#         if positionmanager.is_open:
#             unrealized_pnl = dataloader.get_unrealized_pnl(config.SYMBOL)
#             futures_entry_side = positionmanager.get_futures_entry_side()
#             if unrealized_pnl < config.STOP_LOSS_THRESHOLD:
#                 logger.info(
#                     f"[STOP-LOSS] Closing due to PnL {unrealized_pnl} < {config.STOP_LOSS_THRESHOLD}"
#                 )
#                 if positionmanager.side == "LONG":
#                     spot_closed = ordermanager.close_position(config.SYMBOL, False)
#                 else:
#                     trader_spot.margin_buy(config.SYMBOL, size)
#                     trader_spot.margin_repay(config.SYMBOL, size)
#                     spot_closed = True
#                 futures_closed = ordermanager.close_position(config.SYMBOL, True)
#                 positionmanager.close(
#                     spot_exit_price=spot_price, futures_exit_price=futures_price
#                 )
#                 continue  # If we close the position we move to the next iteration
#             elif positionmanager.side == "LONG" and strategy.check_is_long_spread_exit(
#                 zscore
#             ):  # zscore > -config.Z_EXIT:
#                 # Close LONG spread
#                 spot_closed = ordermanager.close_position(config.SYMBOL, False) # trader_spot.spot_sell(config.SYMBOL, size)
#                 futures_closed = ordermanager.close_position(config.SYMBOL, True) # trader_futures.futures_close_position(config.SYMBOL, futures_entry_side, size)
#             elif (
#                 positionmanager.side == "SHORT"
#                 and strategy.check_is_short_spread_exit(zscore)
#             ):  # and zscore < config.Z_EXIT:
#                 # Close SHORT spread
#                 trader_spot.margin_buy(config.SYMBOL, size)
#                 trader_spot.margin_repay(config.SYMBOL, size)
#                 spot_closed = True
#                 futures_closed = ordermanager.close_position(config.SYMBOL, True)
#             else:
#                 logger.debug(positionmanager.position_info())
#                 continue
#             # === HISTORY LOGGING ===
#             if strategy.check_is_short_spread_exit(
#                 zscore
#             ) or strategy.check_is_long_spread_exit(zscore):
#                 exit_time = datetime.now(tz=timezone.utc)
#                 spot_pnl = positionmanager.calc_closing_spot_pnl(spot_price)
#                 futures_pnl = positionmanager.calc_closing_futures_pnl(futures_price)
#                 total_pnl = positionmanager.calc_total_pnl(
#                     exit_spot_price=spot_price, exit_futures_price=futures_price
#                 )
#                 cumulative_pnl += total_pnl
#                 trade_event = historymanager.format_trade_event(
#                     timestamp=exit_time,
#                     action="CLOSE",
#                     position_side=positionmanager.side,
#                     spot_price=spot_price,
#                     futures_price=futures_price,
#                     quantity=size,
#                     extra_info={
#                         "Spot PnL (USD)": round(spot_pnl, 2),
#                         "Futures PnL (USD)": round(futures_pnl, 2),
#                         "Total Net PnL (USD)": round(total_pnl, 2),
#                         "Cumulative Pnl": round(cumulative_pnl, 2),
#                     },
#                 )
#                 logger.success(
#                     f"[TRADE] Closed {positionmanager.side} spread. PNL: {total_pnl}, Z: {zscore:.3f}"
#                 )
#                 historymanager.log_event(trade_event)
#                 positionmanager.close(
#                     spot_exit_price=spot_price, futures_exit_price=futures_price
#                 )
#                 continue
#
#         # ENTRY LOGIC
#         # if position == 0:
#         if not positionmanager.is_open:
#             if strategy.check_is_short_spread_entry(
#                 zscore, exp_profit, exp_tc
#             ):  # zscore > config.Z_ENTRY and exp_profit >= exp_tc:
#                 # SHORT spread (simulated spot short)
#                 trader_spot.margin_borrow(config.SYMBOL, size)
#                 trader_spot.margin_sell(config.SYMBOL, size)  # SHORT Spot
#                 spot_opened = True
#                 futures_opened = ordermanager.futures_buy(config.SYMBOL, size)  # LONG Fut
#                 position_side = "SHORT"
#             elif strategy.check_is_long_spread_entry(
#                 zscore, exp_profit, exp_tc
#             ):  # zscore < -config.Z_ENTRY and exp_profit >= exp_tc:
#                 # LONG spread (real spot buy)
#                 spot_opened = ordermanager.spot_buy(config.SYMBOL, size)  # LONG Spot
#                 futures_opened = ordermanager.futures_sell(config.SYMBOL, size)  # SHORT Fut
#                 position_side = "LONG"
#             else:
#                 logger.info("Position entry criterion not met, not trying.")
#                 continue
#
#             if not (spot_opened and futures_opened):
#                 logger.warning(f"One of legs are not executed, force closing all positions")
#                 ordermanager.close_position(config.SYMBOL, True)
#                 ordermanager.close_position(config.SYMBOL, False)
#                 continue
#
#             if strategy.check_is_long_spread_entry(
#                 zscore, exp_profit, exp_tc
#             ) or strategy.check_is_short_spread_entry(zscore, exp_profit, exp_tc):
#                 entry_time = datetime.now(tz=timezone.utc)
#                 positionmanager.open(
#                     side=position_side,  # This is always defined
#                     spot_price=spot_price,
#                     futures_price=futures_price,
#                     size=size,
#                 )
#                 logger.success(
#                     f"[TRADE] Opened {position_side} spread. Exp Profit {exp_profit}, Exp Cost {exp_tc}"
#                 )
#                 # History Logging
#                 trade_event = historymanager.format_trade_event(
#                     timestamp=entry_time,  # This is always defined
#                     action="OPEN",
#                     position_side=positionmanager.side,
#                     spot_price=positionmanager.spot_entry_price,
#                     futures_price=positionmanager.futures_entry_price,
#                     quantity=positionmanager.size,
#                     extra_info={"Expected TC": exp_tc, "Expected Profit": exp_profit},
#                 )
#                 historymanager.log_event(trade_event)
#
#         time.sleep(config.SLEEP_TIME)
#
#         logger.info(f"Cumulative pnl: {cumulative_pnl}")
#     except Exception as e:
#         logger.error(f"[ERROR] {e}")
#         time.sleep(config.SLEEP_TIME)
