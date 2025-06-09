
from decimal import Decimal
from typing import Any, Dict, Literal
from alpheast.models.signal import Signal
from alpheast.position_sizing.base_position_sizing import BasePositionSizing


class FixedQuantitySizing(BasePositionSizing):
    def __init__(self, quantity: int):
        self.quantity = Decimal(str(quantity))

    def calculate_quantity(
        self,
        symbol: str,
        direction: Signal,
        current_price: Decimal,
        portfolio_cash: Decimal,
        portfolio_holdings: Dict[str, Decimal],
        **kwargs: Any
    ) -> Decimal:
        if direction == Signal.BUY:
            return self.quantity
        elif direction == Signal.SELL:
            return portfolio_holdings.get(symbol, Decimal("0"))
        return Decimal("0")