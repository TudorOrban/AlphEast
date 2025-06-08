
from decimal import Decimal
from typing import Any, Dict, Literal
from src.backtesting_engines.event_driven_engine.position_sizing.base_position_sizing import BasePositionSizing


class FixedQuantitySizing(BasePositionSizing):
    def __init__(self, quantity: int):
        self.quantity = Decimal(str(quantity))

    def calculate_quantity(
        self,
        symbol: str,
        direction: Literal["BUY", "SELL"],
        current_price: Decimal,
        portfolio_cash: Decimal,
        portfolio_holdings: Dict[str, Decimal],
        **kwargs: Any
    ) -> Decimal:
        if direction == "BUY":
            return self.quantity
        elif direction == "SELL":
            return portfolio_holdings.get(symbol, Decimal("0"))
        return Decimal("0")