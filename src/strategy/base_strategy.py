
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from data.eod_prices.model import EODPrice
from strategy.models.signal import Signal


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    Users implement concrete strategies by inheriting from this class.
    """
    def __init__(self, symbol: str, **kwargs: Any):
        """
        Initializes the strategy with common parameters.
        Concrete strategies should call super().__init__() and then set their specific parameters.
        """
        if not symbol:
            raise ValueError("Strategy must be initialized with a target symbol")
        self.symbol: str = symbol
        self.params: Dict[str, Any] = kwargs

        self.portfolio: Any = None
        self.history_manager: Any = None

    def set_environment(self, portfolio_instance: Any, history_manager_instance: Any):
        self.portfolio = portfolio_instance
        self.history_manager = history_manager_instance

    @abstractmethod
    def initialize(self):
        """
        Called once at the beginning of the backtest.
        Use for any initial setup logic.
        """
        pass

    @abstractmethod
    def on_data(self, current_bar: EODPrice, history_window: List[EODPrice]) -> Signal:
        """
        Called for each new bar (EODPrice) as the backtest progresses chronologically.
        
        Args:
            current_bar: The latest EODPrice bar being processed.
            history_window: A list of relevant historical EODPrice bars
                            (e.g., enough for indicator calculation).
                            Provided by the Backtester.

        Returns:
            A Signal (BUY, SELL, HOLD) indicating the desired action.
        """
        pass