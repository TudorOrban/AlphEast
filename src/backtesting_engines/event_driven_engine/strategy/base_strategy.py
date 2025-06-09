
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict

from src.backtesting_engines.event_driven_engine.models.event import MarketEvent, SignalEvent
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.models.signal import Signal


class BaseStrategy(ABC):
    """
    Abstract base class for the trading strategy in the new event-driven backtesting engine.
    Strategies process MarketEvents and generate SignalEvents.
    """
    def __init__(self, event_queue: EventQueue, symbol: str, **kwargs: Any):
        if not symbol:
            raise ValueError("Strategy must be initialized with a target symbol.")
        self.event_queue = event_queue
        self.symbol: str = symbol
        self.params: Dict[str, Any] = kwargs
        logging.info(f"{self.__class__.__name__} initialized for {symbol} with params: {kwargs}")

    @abstractmethod
    def on_market_event(self, event: MarketEvent):
        """
        Called when a new MarketEvent (e.g. a new bar of data) is received.
        Strategies should implement their trading logic here.
        """
        pass

    def _put_signal_event(
        self,
        timestamp: datetime,
        direction: Signal,
        strength: float = 1.0
    ):
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=timestamp,
            direction=direction,
            strength=strength
        )
        self.event_queue.put(signal_event)
        logging.debug(f"Strategy for {self.symbol} issued {direction} signal on {timestamp.date()}.")