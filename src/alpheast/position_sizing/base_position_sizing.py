
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Literal

from alpheast.models.signal import Signal


class BasePositionSizing(ABC):
    @abstractmethod
    def calculate_quantity(
        self,
        symbol: str,
        direction: Signal,
        current_price: Decimal,
        portfolio_cash: Decimal,
        portfolio_holdings: Dict[str, Decimal],
        **kwargs: Any
    ) -> Decimal:
        """
        Calculates the quantity to trade based on the given context.
        """
        pass