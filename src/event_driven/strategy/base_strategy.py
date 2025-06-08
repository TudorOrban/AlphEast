
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, Optional

from src.event_driven.models.event import MarketEvent, SignalEvent
from src.event_driven.event_queue import EventQueue
from strategy.models.signal import Signal


class NewBaseStrategy(ABC):
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
        logging.info(f"self.__class__.__name__ initialized for {symbol} with params: {kwargs}")

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
        strength: float = 1.0,
        quantity: Optional[Decimal] = None
    ):
        """
        Helper method for strategy to create and put a SignalEvent onto the queue.
        """
        signal_direction_str = direction.value

        if signal_direction_str in ["BUY", "SELL"]:
            signal_event = SignalEvent(
                symbol=self.symbol,
                timestamp=timestamp,
                direction=signal_direction_str,
                strength=strength,
                quantity=quantity
            )
            self.event_queue.put(signal_event)
            logging.debug(f"Strategy for {self.symbol} issued {signal_direction_str} signal on {timestamp.date()}.")