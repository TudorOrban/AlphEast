from abc import ABC
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Literal, Optional


class Event(ABC):
    """
    Base class for all events
    """
    @property
    def type(self) -> str:
        raise NotImplementedError("Subclasses must define the 'type' property.")
    
class MarketEvent(Event):
    """
    Handles the receipt of new market data (e.g. a new bar for a specific symbol)
    """
    def __init__(self, symbol: str, timestamp: datetime, data: Dict[str, Any]):
        self._type = "MARKET"
        self.symbol = symbol
        self.timestamp = timestamp
        self.data = data

    @property
    def type(self) -> str:
        return self._type
    
    def __repr__(self):
        return f"MarketEvent(symbol='{self.symbol}', timestamp={self.timestamp.date()}, data={self.data.get('close', 'N/A')})"
    
class SignalEvent(Event):
    """
    Handles the generation of a trade signal by a strategy.
    """
    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        direction: Literal["BUY", "SELL", "HOLD"],
        strength: float = 1.0,
        quantity: Optional[Decimal] = None
    ):
        self._type = "SIGNAL"
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.strength = strength
        self.quantity = quantity

    @property
    def type(self) -> str:
        return self._type
    
    def __repr__(self):
        return f"SignalEvent(symbol='{self.symbol}', timestamp={self.timestamp.date()}, direction='{self.direction}')"

class OrderEvent(Event):
    """
    Handles placing an order with the execution handler.
    Comes from the portfolio manager based on signal events.
    """
    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        direction: Literal["BUY", "SELL"],
        quantity: Decimal,
        order_type: Literal["MARKET", "LIMIT"] = "MARKET",
        price: Optional[Decimal] = None
    ):
        if not (isinstance(quantity, Decimal) and quantity > Decimal("0")):
            raise ValueError("Order quantity must be a positive Decimal.")
        if order_type == "LIMIT" and price is None:
            raise ValueError("Limit orders require a price.")
        if direction not in ["BUY", "SELL"]:
            raise ValueError("Order direction must be 'BUY' or 'SELL'")
        
        self._type = "ORDER"
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.quantity = quantity
        self.order_type = order_type
        self.price = price

    @property
    def type(self) -> str:
        return self._type

    def __repr__(self):
        return (
            f"OrderEvent(symbol='{self.symbol}', timestamp={self.timestamp.date()}, "
            f"direction='{self.direction}', quantity={self.quantity}, type='{self.order_type}'"
            f"{f', price={self.price}' if self.price else ''})"
        )
    
class FillEvent(Event):
    """
    Encapsulates the notion of an order being filled, with a quantity and an actual fill prices.
    Comes from the execution handler.
    """
    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        direction: Literal["BUY", "SELL"],
        quantity: Decimal,
        fill_price: Decimal,
        commission: Decimal = Decimal('0.0'),
        successful: bool = True 
    ):
        if not (isinstance(quantity, Decimal) and quantity > Decimal('0')):
            raise ValueError("Fill quantity must be a positive Decimal.")
        if not (isinstance(fill_price, Decimal) and fill_price > Decimal('0')):
            raise ValueError("Fill price must be a positive Decimal.")
        if direction not in ["BUY", "SELL"]:
            raise ValueError("Fill direction must be 'BUY' or 'SELL'.")

        self._type = "FILL"
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.successful = successful

    @property
    def type(self) -> str:
        return self._type

    def __repr__(self):
        return (
            f"FillEvent(symbol='{self.symbol}', timestamp={self.timestamp.date()}, "
            f"direction='{self.direction}', quantity={self.quantity}, fill_price={self.fill_price:.2f}, "
            f"commission={self.commission:.2f}, successful={self.successful})"
        )