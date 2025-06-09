from abc import ABC, abstractmethod

from alpheast.events.event import MarketEvent, OrderEvent


class ExecutionHandler(ABC):
    """
    Abstract base class for all execution handlers.
    Subclasses must implement methods for processing order events and sending fill events.
    """
    @abstractmethod
    def on_market_event(self, event: MarketEvent):
        """
        Updates internal market data cache, needed for realistic fills.
        """
        raise NotImplementedError("Subclasses must implement on_market_event()")
    
    @abstractmethod
    def on_order_event(self, event: OrderEvent):
        """
        Processes an OrderEvent and, upon successfuly simulation,
        generates a FillEvent and puts it onto the event queue.
        """
        raise NotImplementedError("Subclasses must implement on_order_event()")