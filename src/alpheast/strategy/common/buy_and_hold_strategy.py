
import logging
from typing import Any

from alpheast.events.event import MarketEvent
from alpheast.strategy.base_strategy import BaseStrategy
from alpheast.models.signal import Signal


class BuyAndHoldStrategy(BaseStrategy):
    """
    A simple Buy and Hold trading strategy.

    This strategy buys the specified symbol once at the first available market
    event and holds it for the duration of the backtest.

    :param symbol: The financial instrument symbol this strategy will trade.
    :param kwargs: Arbitrary keyword arguments passed to the base strategy.
    """
    def __init__(self, symbol: str, **kwargs: Any):
        super().__init__(symbol, **kwargs)
        self._bought_initial_position = False
        logging.info(f"BuyAndHoldStrategy initialized for {self.symbol}")

    def on_market_event(self, event: MarketEvent):
        if event.symbol != self.symbol:
            return

        if not self._bought_initial_position:
            self._put_signal_event(event.timestamp, Signal.BUY)
            self._bought_initial_position = True
            logging.info(f"BuyAndHoldStrategy: Initial BUY signal for {self.symbol} at {event.timestamp.date()}")
        else:
            # Hold the position
            pass