
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict, Optional

from alpheast.events.event import MarketEvent, SignalEvent
from alpheast.events.event_queue import EventQueue
from alpheast.models.signal import Signal


class BaseStrategy(ABC):
    """
    Abstract base class for the trading strategy in the new event-driven backtesting engine.
    Strategies process MarketEvents and generate SignalEvents.
    """
    def __init__(self, symbol: str, **kwargs: Any):
        if not symbol:
            raise ValueError("Strategy must be initialized with a target symbol.")
        self.event_queue: Optional[EventQueue] = None
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

    def set_event_queue(self, event_queue: EventQueue):
        self.event_queue = event_queue

    def _put_signal_event(
        self,
        timestamp: datetime,
        direction: Signal,
        strength: float = 1.0
    ):
        if self.event_queue is None:
            raise RuntimeError("Event queue not set for strategy. Call set_event_queue() first.")
        
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=timestamp,
            direction=direction,
            strength=strength
        )
        self.event_queue.put(signal_event)
        logging.debug(f"Strategy for {self.symbol} issued {direction} signal on {timestamp.date()}.")