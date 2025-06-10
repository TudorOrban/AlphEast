from datetime import date
from typing import List

from alpheast.models.interval import Interval


class BacktestConfig:
    def __init__(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: Interval = Interval.DAILY,
        initial_cash: float = 100_000.0,
        transaction_cost_percent: float = 0.001,
        slippage_percent: float = 0.0005
    ):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.initial_cash = initial_cash
        self.transaction_cost_percent = transaction_cost_percent
        self.slippage_percent = slippage_percent

        # Validation
        if not self.symbols:
            raise ValueError("Symbols list cannot be empty.")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date.")
        if self.initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")
