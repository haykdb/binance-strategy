# bot.py

from loguru import logger
import time
import config
from margin_trader import SpotTrader
from futures_trader import FuturesTrader # import futures_trader as futures
from strategy import StrategyCalculator # import strategy
from utils import DataLoader # import utils
from binance.client import Client
from history_logger import HistoryLogger# import history_logger
from datetime import datetime, timezone, date

LOGGER = f"/Users/admin/PycharmProjects/binance-strategy/logs/{date.today()}.log"
logger.add(LOGGER)

# TODO Add Transaction Costs ✅
# TODO Make better live pnl tracking ✅
# TODO Add Trade Class to record all trades, monitor all positions, keep in history ✅
# TODO Add Position Management, Close and Liquidate if positions get too big or too small or: Check before opening a trade that position is already open or not ✅
# TODO Make Position Manager More Robust
# Todo Integrate Position Manager in the bot
# TODO Divide Bot into different code sections

# === CONNECT ===
spot_client = Client(config.SPOT_API_KEY, config.SPOT_API_SECRET, testnet=config.USE_TESTNET)
futures_client = Client(config.FUTURES_API_KEY, config.FUTURES_API_SECRET, testnet=config.USE_TESTNET)

# === MANUALLY SET TESTNET URLs ===
if config.USE_TESTNET:
    spot_client.API_URL = 'https://testnet.binance.vision'  # ✅ Force Spot Testnet
    futures_client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'  # ✅ Force Futures Testnet

futures_client.futures_change_leverage(symbol=config.SYMBOL, leverage=config.LEVERAGE)

# === INITIATING ALL CLASSES ===
trader_spot = SpotTrader(spot_client=spot_client)
trader_futures = FuturesTrader(futures_client=futures_client)
strategy = StrategyCalculator(configs=config)
dataloader = DataLoader(spot_client=spot_client, futures_client=futures_client)
historymanager = HistoryLogger(config=config)


# === STATE ===
position = 0  # 0 = no position, 1 = long spread, -1 = short spread
entry_side = None
entry_spot_price = None  # Save the spot price at trade entry
total_pnl = 0
cumulative_pnl = 0

logger.info("[BOT] Starting...")

while True:
    try:
        spot_price = round(dataloader.get_spot_price(config.SYMBOL), 4)
        futures_price = round(dataloader.get_futures_price(config.SYMBOL), 4)
        spread = strategy.update_spread(spot_price, futures_price)
        zscore = strategy.calculate_zscore()

        exp_profit = strategy.calculate_expected_profit()
        exp_tc = 0 # strategy.calculate_expected_tc(spot_price, futures_price)

        if zscore is None:
            logger.info(f"Building history ({len(strategy.spread_history)}/{config.LOOKBACK})...")
            time.sleep(config.SLEEP_TIME)
            continue

        size = round(dataloader.calculate_trade_size(config.CAPITAL_PER_TRADE, spot_price, config.SYMBOL), 1)

        logger.info(f"[SPREAD] Spot: {spot_price:.4f}, Futures: {futures_price:.4f}, Spread: {spread:.4f}, Z: {zscore:.2f}, TC: {exp_tc}, PF: {exp_profit}")

        # STOP-LOSS CHECK
        if position != 0:
            unrealized_pnl = dataloader.get_unrealized_pnl(config.SYMBOL)
            if unrealized_pnl < config.STOP_LOSS_THRESHOLD:
                logger.info(f"[STOP-LOSS] Closing due to PnL {unrealized_pnl} < {config.STOP_LOSS_THRESHOLD}")
                if position == 1:
                    trader_spot.spot_sell(config.SYMBOL, size)
                else:
                    trader_spot.margin_buy(config.SYMBOL, size)
                    trader_spot.margin_repay(config.SYMBOL, size)
                trader_futures.futures_close_position(config.SYMBOL, entry_side, size)
                position = 0
                continue

        # ENTRY LOGIC
        if position == 0:
            if zscore > config.Z_ENTRY and exp_profit >= exp_tc:
                # SHORT spread (simulated spot short)
                trader_spot.margin_borrow(config.SYMBOL, size)
                trader_spot.margin_sell(config.SYMBOL, size)
                trader_futures.futures_open_long(config.SYMBOL, size)
                entry_spot_price = spot_price
                position = -1
                entry_side = 'BUY'
                logger.success(f"[TRADE] Opened SHORT spread. Exp Profit {exp_profit}, Exp Cost {exp_tc}")
                # History Logging
                entry_time = datetime.now(tz=timezone.utc)
                trade_event = historymanager.format_trade_event(
                    timestamp=entry_time,
                    action='OPEN',
                    position_side='LONG' if position == 1 else 'SHORT',
                    spot_price=spot_price,
                    futures_price=futures_price,
                    quantity=size,
                    extra_info={
                        'Expected TC': exp_tc,
                        'Expected Profit': exp_profit
                    }
                )
                historymanager.log_event(trade_event)

            elif zscore < -config.Z_ENTRY and exp_profit >= exp_tc:
                # LONG spread (real spot buy)
                trader_spot.spot_buy(config.SYMBOL, size)
                trader_futures.futures_open_short(config.SYMBOL, size)
                entry_spot_price = spot_price
                position = 1
                entry_side = 'SELL'
                logger.success(f"[TRADE] Opened LONG spread. Exp Profit {exp_profit}, Exp Cost {exp_tc}")
                # History Logging
                entry_time = datetime.now(tz=timezone.utc)
                trade_event = historymanager.format_trade_event(
                    timestamp=entry_time,
                    action='OPEN',
                    position_side='LONG' if position == 1 else 'SHORT',
                    spot_price=spot_price,
                    futures_price=futures_price,
                    quantity=size,
                    extra_info={
                        'Expected TC': exp_tc,
                        'Expected Profit': exp_profit
                    }
                )
                historymanager.log_event(trade_event)



        # EXIT LOGIC
        elif position == 1 and zscore > -config.Z_EXIT:
            # Close LONG spread
            trader_spot.spot_sell(config.SYMBOL, size)
            trader_futures.futures_close_position(config.SYMBOL, entry_side, size)
            unrealized_futures_pnl = dataloader.get_unrealized_pnl(config.SYMBOL) # - 2 * futures_price * config.TC * size
            spot_pnl = (spot_price - entry_spot_price) * size #- (spot_price + entry_spot_price) * config.TC * size
            total_pnl = unrealized_futures_pnl + spot_pnl
            logger.success(f"[TRADE] Closed LONG spread. PNL: {total_pnl}")
            cumulative_pnl += total_pnl

            # History Logging
            exit_time = datetime.now(tz=timezone.utc)

            trade_event = historymanager.format_trade_event(
                timestamp=exit_time,
                action='CLOSE',
                position_side='LONG' if position == 1 else 'SHORT',
                spot_price=spot_price,
                futures_price=futures_price,
                quantity=size,
                extra_info={
                    'Spot PnL (USD)': round(spot_pnl, 2),
                    'Futures PnL (USD)': round(unrealized_futures_pnl, 2),
                    'Total Net PnL (USD)': round(total_pnl, 2),
                    'Cumulative Pnl': round(cumulative_pnl, 2),
                }
            )
            historymanager.log_event(trade_event)
            position = 0

        elif position == -1 and zscore < config.Z_EXIT:
            # Close SHORT spread
            trader_spot.margin_buy(config.SYMBOL, size)
            trader_spot.margin_repay(config.SYMBOL, size)
            trader_futures.futures_close_position(config.SYMBOL, entry_side, size)
            unrealized_futures_pnl = dataloader.get_unrealized_pnl(config.SYMBOL) #- 2 * futures_price * config.TC * size
            spot_pnl = (entry_spot_price - spot_price) * size #- (spot_price + entry_spot_price) * config.TC * size
            total_pnl = unrealized_futures_pnl + spot_pnl
            logger.success(f"[TRADE] Closed SHORT spread. PNL: {total_pnl}")
            cumulative_pnl += total_pnl
            # History Logging
            exit_time = datetime.now(tz=timezone.utc)

            trade_event = historymanager.format_trade_event(
                timestamp=exit_time,
                action='CLOSE',
                position_side='LONG' if position == 1 else 'SHORT',
                spot_price=spot_price,
                futures_price=futures_price,
                quantity=size,
                extra_info={
                    'Spot PnL (USD)': round(spot_pnl, 2),
                    'Futures PnL (USD)': round(unrealized_futures_pnl, 2),
                    'Total Net PnL (USD)': round(total_pnl, 2),
                    'Cumulative Pnl': round(cumulative_pnl, 2),
                }
            )
            historymanager.log_event(trade_event)
            position = 0

        time.sleep(config.SLEEP_TIME)

        logger.info(f"Cumulative pnl: {cumulative_pnl}")
    except Exception as e:
        logger.error(f"[ERROR] {e}")
        time.sleep(config.SLEEP_TIME)
