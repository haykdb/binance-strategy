from pathlib import Path

DIR = Path("/Users/admin/PycharmProjects/BinanceBot/data")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from binancetools.binance_1s_downloader import get_all_coins
from loguru import logger


class Coin:
    SPOT_PATTERN = "{ticker}_spot.csv"
    FUTURES_PATTERN = "{ticker}_futures.csv"

    def __init__(self, ticker):
        self.ticker = ticker

    def get_futures_data(self) -> pd.DataFrame:
        return pd.read_csv(
            DIR / self.FUTURES_PATTERN.format(ticker=self.ticker),
            index_col="timestamp",
            parse_dates=True,
        )

    def get_spot_data(self) -> pd.DataFrame:
        return pd.read_csv(
            DIR / self.SPOT_PATTERN.format(ticker=self.ticker),
            index_col="timestamp",
            parse_dates=True,
        )

    def get_combined_data(self) -> pd.DataFrame:
        spot = self.get_spot_data()
        futures = self.get_futures_data()
        return pd.DataFrame(
            {"spot": round(spot["close"], 3), "futures": round(futures["close"], 3)}
        ).dropna()


class BasisStrategy:
    TC = 0.0004

    def __init__(
        self,
        ticker: str,
        lookback: int = 60,
        capital: int = 1000,
        leverage: int = 1,
        z_entry: float = 1.5,
        z_exit: float = 0.5,
    ):
        self.coin = Coin(ticker)
        self.lookback = lookback
        self.capital = capital
        self.leverage = leverage
        self.z_entry = z_entry
        self.z_exit = z_exit

    def get_data(self):
        return self.coin.get_combined_data()

    def calc_spread_basis(self) -> pd.DataFrame:
        df = self.get_data()
        df["abs_basis"] = df["spot"] - df["futures"]
        df["mean_abs_basis"] = df["abs_basis"].rolling(self.lookback).mean()
        df["abs_zscore"] = (
            df["abs_basis"] - df["abs_basis"].rolling(self.lookback).mean()
        ) / df["abs_basis"].rolling(self.lookback).std()
        df["expected_profit"] = (
            df["abs_basis"] - df["abs_basis"].rolling(self.lookback).mean()
        )
        df["expected_tc"] = 2 * df["spot"] * self.TC
        return df

    def calc_mean_spread(self) -> float:
        df = self.calc_spread_basis()
        return df["abs_basis"].mean()

    def calc_mean_spot(self) -> float:
        df = self.get_data()
        return df["spot"].mean()

    def calc_mean_futures(self) -> float:
        df = self.get_data()
        return df["futures"].mean()

    def calc_backtest(self):
        capital_per_trade = self.capital
        leverage = self.leverage
        lookback = self.lookback  # in minutes
        z_entry = self.z_entry
        z_exit = self.z_exit

        position = 0
        entry_price = (0, 0)
        pnl = []
        entries = []
        exits = []

        df = self.calc_spread_basis()
        for i in range(lookback, len(df)):
            row = df.iloc[i]
            timestamp = row.name

            if position == 0:
                # Entry signals
                if (
                    row["abs_zscore"] > z_entry
                    and abs(row["expected_profit"]) >= row["expected_tc"]
                ):
                    # Spread is wide: short spot, long futures
                    position = -1
                    entry_price = (row["spot"], row["futures"])
                    entries.append((timestamp, position))

                elif (
                    row["abs_zscore"] < -z_entry
                    and abs(row["expected_profit"]) >= row["expected_tc"]
                ):
                    # Spread is tight: long spot, short futures
                    position = 1
                    entry_price = (row["spot"], row["futures"])
                    entries.append((timestamp, position))

            elif position == 1 and row["abs_zscore"] > -z_exit:
                # Exit long spread
                exit_price = (row["spot"], row["futures"])
                spot_pnl = (
                    (exit_price[0] - entry_price[0])
                    * capital_per_trade
                    / entry_price[0]
                )
                fut_pnl = (
                    (entry_price[1] - exit_price[1])
                    * capital_per_trade
                    * leverage
                    / entry_price[1]
                )
                total_pnl = spot_pnl + fut_pnl - 4 * capital_per_trade * self.TC
                pnl.append(total_pnl)
                exits.append((timestamp, position, total_pnl))
                position = 0

            elif position == -1 and row["abs_zscore"] < z_exit:
                # Exit short spread
                exit_price = (row["spot"], row["futures"])
                spot_pnl = (
                    (entry_price[0] - exit_price[0])
                    * capital_per_trade
                    / entry_price[0]
                )
                fut_pnl = (
                    (exit_price[1] - entry_price[1])
                    * capital_per_trade
                    * leverage
                    / entry_price[1]
                )
                total_pnl = spot_pnl + fut_pnl - 4 * capital_per_trade * self.TC
                pnl.append(total_pnl)
                exits.append((timestamp, position, total_pnl))
                position = 0
        return pnl, entries, exits

    def calc_pnl_series(self) -> pd.Series:
        pnls, _, _ = self.calc_backtest()
        return pnls

    def calc_pnl(self) -> float:
        return sum(self.calc_pnl_series())

    def calc_sharpe(self) -> float:
        pnl_series = self.calc_pnl_series()
        if len(pnl_series) > 1:
            return (
                np.array(pnl_series).mean()
                / np.array(pnl_series).std()
                * np.sqrt(252 * 24 * 60)
            )
        return 0.0

    def calc_num_of_trades(self) -> float:
        pnl_series = self.calc_pnl_series()
        return len(pnl_series)

    def calc_profit_per_trade(self) -> float:
        return self.calc_pnl() / self.calc_num_of_trades()

    def calc_accuracy(self) -> float:
        pnls = self.calc_pnl_series()
        binary = [1 if pnl > 0 else 0 for pnl in pnls]
        return sum(binary) / len(binary)

    def plot_graph(self):
        # === Plot basis with entry markers ===
        df = self.calc_spread_basis()
        _, entries, _ = self.calc_backtest()

        fig, ax = plt.subplots(figsize=(14, 6))
        df["abs_basis"].plot(
            ax=ax, title=f"{self.coin.ticker} Absolute Basis with Trade Entries"
        )
        df["abs_basis"].rolling(self.lookback).mean().plot(ax=ax, title="Rolling Mean")
        # ax.axhline(df["abs_basis"].mean(), color='red', linestyle='--', label='Mean Basis')

        # Plot triangles for entry positions
        long_entries_x = [t for t, p in entries if p == 1]
        long_entries_y = [df.loc[t, "abs_basis"] for t in long_entries_x]
        short_entries_x = [t for t, p in entries if p == -1]
        short_entries_y = [df.loc[t, "abs_basis"] for t in short_entries_x]

        ax.scatter(
            long_entries_x,
            long_entries_y,
            marker="^",
            color="green",
            s=100,
            label="Long Entry",
        )
        ax.scatter(
            short_entries_x,
            short_entries_y,
            marker="v",
            color="red",
            s=100,
            label="Short Entry",
        )

        # Only show unique legend entries
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        plt.show(block=True)


if __name__ == "__main__":
    strat = BasisStrategy(ticker="EOSUSDT", lookback=120)
    pnls = strat.calc_pnl_series()

    symbols = get_all_coins()
    i = 1
    res = {}
    profitable = []
    failed_symbols = []
    for symbol in symbols:
        try:
            strat = BasisStrategy(
                ticker=symbol,
                lookback=120,
            )
            pnl = strat.calc_profit_per_trade()
            res[symbol] = pnl
            if pnl > 0:
                profitable.append(symbol)
            logger.success(
                f"{symbol} is succesfully calculated, {i}/{len(symbols)} completed..."
            )
        except:
            failed_symbols.append(symbol)
            logger.error(f"Failed for {symbol}")
            i += 1
            continue
        i += 1
    print(res)
