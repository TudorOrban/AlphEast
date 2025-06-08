
from collections import deque
from decimal import Decimal
import logging
from typing import Any
from src.backtesting_engines.event_driven_engine.models.event import MarketEvent
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.strategy.base_strategy import NewBaseStrategy
from src.shared.signal import Signal


class SMACrossoverStrategy(NewBaseStrategy):
    """
    A Simple Moving Average (SMA) Crossover trading strategy.
    Generates BUY/SELL signals based on fast SMA crossing above/below slow SMA.
    """
    def __init__(self, event_queue: EventQueue, symbol: str, fast_period: int, slow_period: int, **kwargs: Any):
        super().__init__(event_queue, symbol, **kwargs)
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
        self.fast_period = fast_period
        self.slow_period = slow_period

        self._closes_history = deque(maxlen=self.slow_period)
        self._has_position = False

    def on_market_event(self, event: MarketEvent):
        if event.symbol != self.symbol:
            return
        
        current_close = Decimal(str(event.data["close"]))
        self._closes_history.append(current_close)

        if len(self._closes_history) < self.slow_period:
            logging.debug(f"Not enough history for {self.symbol} on {event.timestamp.date()}. Need {self.slow_period}, have {len(self._closes_history)}.")
            return
        
        fast_sma_sum_list = list(self._closes_history)[-self.fast_period:]
        fast_sma = sum(fast_sma_sum_list, Decimal('0')) / self.fast_period
        
        slow_sma_sum_list = list(self._closes_history)
        slow_sma = sum(slow_sma_sum_list, Decimal('0')) / self.slow_period
        
        if fast_sma > slow_sma and not self._has_position:
            self._put_signal_event(event.timestamp, Signal.BUY, quantity=Decimal("10"))
            self._has_position = True
        elif fast_sma < slow_sma and self._has_position:
            self._put_signal_event(event.timestamp, Signal.SELL)
            self._has_position = False
        else:
            pass