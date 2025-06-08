
from typing import List

import pandas as pd
from src.backtesting_engines.simple_engine.strategy.base_strategy import BaseStrategy
from src.data.eod_prices.model import EODPrice
from src.shared.signal import Signal


class BasicStrategy(BaseStrategy):
    def __init__(self, symbol: str, fast_period: int = 10, slow_period: int = 50):
        super().__init__(symbol)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def initialize(self):
        pass

    def on_data(self, current_bar: EODPrice, history_window: List[EODPrice]) -> Signal:
        required_data_points = self.slow_period + 1
        if len(history_window) + 1 < required_data_points:
            return Signal.HOLD
        
        all_relevant_bars = history_window + [current_bar]

        closes = pd.Series([bar.close for bar in all_relevant_bars])

        fast_ma = closes.iloc[-self.fast_period:].mean()
        slow_ma = closes.iloc[-self.slow_period:].mean()

        if fast_ma > slow_ma and self.portfolio.get_holding_quantity(self.symbol) == 0:
            return Signal.BUY
        elif fast_ma < slow_ma and self.portfolio.get_holding_quantity(self.symbol) > 0:
            return Signal.SELL
        else:
            return Signal.HOLD