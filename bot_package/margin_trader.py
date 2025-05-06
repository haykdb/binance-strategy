# margin_trader.py
from loguru import logger
import config
from binance.exceptions import BinanceAPIException
import time


class SpotTrader:

    def __init__(self, spot_client):
        self.spot_client = spot_client

    def margin_borrow(self, asset: str, amount: float):
        if config.USE_TESTNET:
            logger.info(f"[SIMULATION] Would BORROW {amount} {asset} on Spot Testnet.")
        else:
            self.spot_client.create_margin_loan(asset=asset, amount=amount)
            logger.info(f"[MARGIN] Borrowed {amount} {asset}.")

    def margin_sell(self, symbol: str, quantity: float):
        if config.USE_TESTNET:
            logger.info(
                f"[SIMULATION] Would SELL (short) {quantity} {symbol} on Spot Testnet."
            )
        else:
            self.safe_margin_order(
                symbol=symbol, side="SELL", type="MARKET", quantity=quantity
            )
            logger.info(f"[MARGIN] Sold {quantity} {symbol}.")

    def margin_buy(self, symbol: str, quantity: float):
        if config.USE_TESTNET:
            logger.info(
                f"[SIMULATION] Would BUY (cover short) {quantity} {symbol} on Spot Testnet."
            )
        else:
            self.safe_margin_order(
                symbol=symbol, side="BUY", type="MARKET", quantity=quantity
            )
            logger.info(f"[MARGIN] Bought back {quantity} {symbol}.")

    def margin_repay(self, asset: str, amount: float):
        if config.USE_TESTNET:
            logger.info(f"[SIMULATION] Would REPAY {amount} {asset} on Spot Testnet.")
        else:
            self.spot_client.repay_margin_loan(asset=asset, amount=amount)
            logger.info(f"[MARGIN] Repaid {amount} {asset} loan.")

    def spot_buy(self, symbol: str, quantity: float):
        self.safe_spot_order(symbol=symbol, side="BUY", quantity=quantity)
        logger.info(f"[SPOT] Bought {quantity} {symbol}.")

    def spot_sell(self, symbol: str, quantity: float):
        self.safe_spot_order(symbol=symbol, side="SELL", quantity=quantity)
        logger.info(f"[SPOT] Sold {quantity} {symbol}.")

    from binance.exceptions import BinanceAPIException
    import time

    def safe_spot_order(
        self, symbol: str, side: str, quantity: float, max_retries=3, type="MARKET"
    ):
        attempt = 0
        original_quantity = quantity

        while attempt < max_retries:
            try:
                self.spot_client.create_order(
                    symbol=symbol, side=side, type=type, quantity=quantity
                )
                logger.success(f"[SPOT ORDER SUCCESS] {side} {quantity} {symbol}")
                return True

            except BinanceAPIException as e:
                if e.code in (-1013, -4131):  # LOT_SIZE or PERCENT_PRICE
                    logger.warning(
                        f"[SPOT WARNING] Order failed (code {e.code}). Retrying smaller size. Attempt {attempt + 1}/{max_retries}"
                    )
                    quantity = quantity / 2  # Reduce size by half
                    attempt += 1
                    time.sleep(1)
                else:
                    logger.error(f"[SPOT ERROR] Order failed: {e.message}")
                    return False

        logger.error(
            f"[SPOT ERROR] Failed to place spot order after {max_retries} retries. Giving up."
        )
        return False

    from binance.exceptions import BinanceAPIException
    import time

    def safe_margin_order(
        self, symbol: str, side: str, quantity: float, max_retries=3, type="MARKET"
    ):
        attempt = 0

        while attempt < max_retries:
            try:
                self.spot_client.create_margin_order(
                    symbol=symbol, side=side, type=type, quantity=quantity
                )
                print(f"[MARGIN ORDER SUCCESS] {side} {quantity} {symbol}")
                return True

            except BinanceAPIException as e:
                if e.code in (-1013, -4131):
                    print(
                        f"[MARGIN WARNING] Order failed (code {e.code}). Retrying smaller size. Attempt {attempt + 1}/{max_retries}"
                    )
                    quantity = quantity / 2
                    attempt += 1
                    time.sleep(1)
                else:
                    print(f"[MARGIN ERROR] Order failed: {e.message}")
                    return False

        print(
            f"[MARGIN ERROR] Failed to place margin order after {max_retries} retries. Giving up."
        )
        return False


# def margin_borrow(spot_client, asset: str, amount: float):
#     if config.USE_TESTNET:
#         logger.info(f"[SIMULATION] Would BORROW {amount} {asset} on Spot Testnet.")
#     else:
#         spot_client.create_margin_loan(asset=asset, amount=amount)
#         logger.info(f"[MARGIN] Borrowed {amount} {asset}.")

# def margin_sell(spot_client, symbol: str, quantity: float):
#     if config.USE_TESTNET:
#         logger.info(f"[SIMULATION] Would SELL (short) {quantity} {symbol} on Spot Testnet.")
#     else:
#         spot_client.create_margin_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
#         logger.info(f"[MARGIN] Sold {quantity} {symbol}.")
#
# def margin_buy(spot_client, symbol: str, quantity: float):
#     if config.USE_TESTNET:
#         logger.info(f"[SIMULATION] Would BUY (cover short) {quantity} {symbol} on Spot Testnet.")
#     else:
#         spot_client.create_margin_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
#         logger.info(f"[MARGIN] Bought back {quantity} {symbol}.")
#
# def margin_repay(spot_client, asset: str, amount: float):
#     if config.USE_TESTNET:
#         logger.info(f"[SIMULATION] Would REPAY {amount} {asset} on Spot Testnet.")
#     else:
#         spot_client.repay_margin_loan(asset=asset, amount=amount)
#         logger.info(f"[MARGIN] Repaid {amount} {asset} loan.")
#
# def spot_buy(spot_client, symbol: str, quantity: float):
#     spot_client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
#     logger.info(f"[SPOT] Bought {quantity} {symbol}.")
#
# def spot_sell(spot_client, symbol: str, quantity: float):
#     spot_client.create_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
#     logger.info(f"[SPOT] Sold {quantity} {symbol}.")
