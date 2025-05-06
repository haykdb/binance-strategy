# live_monitor.py

from rich.live import Live
from rich.table import Table
from time import sleep


class LiveMonitor:
    def __init__(self, symbol_status, refresh_rate=5):
        self.symbol_status = symbol_status  # Shared dict
        self.refresh_rate = refresh_rate    # In seconds

    def _render_table(self):
        table = Table(title="📊 Live Bot Monitor", expand=True)

        table.add_column("Symbol", justify="left")
        table.add_column("Position", justify="center")
        table.add_column("Signal", justify="center")
        table.add_column("Spot", justify="right")
        table.add_column("Futures", justify="right")
        table.add_column("PnL", justify="right")
        table.add_column("Last Update", justify="right")

        for symbol, data in self.symbol_status.items():
            table.add_row(
                symbol,
                str(data.get("position", "-")),
                str(data.get("signal", "-")),
                f'{data.get("spot", 0):.2f}',
                f'{data.get("futures", 0):.2f}',
                f'{data.get("pnl", 0):.2f}',
                data.get("updated", "-")
            )

        return table

    def run(self):
        with Live(self._render_table(), refresh_per_second=1) as live:
            while True:
                live.update(self._render_table())
                sleep(self.refresh_rate)
