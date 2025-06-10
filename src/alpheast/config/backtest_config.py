from datetime import date
import logging
from typing import List, Optional

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
        
    def log(self):
        logging.info(f"Symbols: {self.symbols}, Start Date: {self.start_date}, End Date: {self.end_date}, Initial Cash: {self.initial_cash}, Interval: {self.interval}, Trans: {self.transaction_cost_percent}")

class BacktestingOptions:
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: Optional[Interval] = None,
        initial_cash: Optional[float] = None,
        transaction_cost_percent: Optional[float] = None,
        slippage_percent: Optional[float] = None
    ):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.initial_cash = initial_cash
        self.transaction_cost_percent = transaction_cost_percent
        self.slippage_percent = slippage_percent

    def validate(self) -> BacktestConfig:
        if not self.symbols:
            raise ValueError("Symbols list cannot be empty.")
        if not self.start_date:
            raise ValueError("Start date must not be None")
        if not self.end_date:
            raise ValueError("End date must not be None")
        if not self.interval:
            raise ValueError("Interval must not be None")
        if not self.initial_cash:
            raise ValueError("Initial cash must not be None")
        
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date.")
        if self.initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")
        
        if not self.transaction_cost_percent:
            self.transaction_cost_percent = 0.001
        if not self.slippage_percent:
            self.slippage_percent = 0.0005
        
        return BacktestConfig(self.symbols, self.start_date, self.end_date, self.interval, self.initial_cash, self.transaction_cost_percent, self.slippage_percent)
    
    def override(self, configuration: "BacktestingOptions"):
        if configuration.symbols is not None:
            self.symbols = configuration.symbols
        if configuration.start_date is not None:
            self.start_date = configuration.start_date
        if configuration.end_date is not None:
            self.end_date = configuration.end_date
        if configuration.interval is not None:
            self.interval = configuration.interval
        if configuration.initial_cash is not None:
            self.initial_cash = configuration.initial_cash