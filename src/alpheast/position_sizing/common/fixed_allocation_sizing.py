
from decimal import Decimal
from typing import Any, Dict, Literal
from alpheast.models.signal import Signal
from alpheast.position_sizing.base_position_sizing import BasePositionSizing


class FixedAllocationSizing(BasePositionSizing):
    def __init__(self, allocation_percent: float):
        self.allocation_percent = Decimal(str(allocation_percent))

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
            cash_to_allocate = portfolio_cash * self.allocation_percent
            return (cash_to_allocate / current_price).quantize(Decimal("1"))
        elif direction == Signal.SELL:
            return portfolio_holdings.get(symbol, Decimal("0"))
        return Decimal("0")