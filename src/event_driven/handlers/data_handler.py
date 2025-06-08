
from abc import ABC, abstractmethod


class DataHandler(ABC):
    """
    Abstract base class for all data handlers.
    Subclasses must implement methods for fetching market data and generating market events.
    """
    @abstractmethod
    def stream_next_market_event(self):
        raise NotImplementedError("Subclasses must implement stream_next_market_event()")
    
    @abstractmethod
    def continue_backtest(self) -> bool:
        raise NotImplementedError("Subclasses must implement continue_backtest()")
    
