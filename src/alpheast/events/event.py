from abc import ABC
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Literal, Optional

from alpheast.models.signal import Signal
from alpheast.events.event_enums import EventType, OrderType


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
    def __init__(
        self, 
        symbol: str, 
        timestamp: datetime, 
        data: Dict[str, Any]
    ):
        self._type = EventType.MARKET
        self.symbol = symbol
        self.timestamp = timestamp
        self.data = data

    @property
    def type(self) -> EventType:
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
        direction: Signal,
        strength: float = 1.0,
    ):
        self._type = EventType.SIGNAL
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.strength = strength

    @property
    def type(self) -> EventType:
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
        order_id: str,
        symbol: str,
        timestamp: datetime,
        direction: Signal,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None
    ):
        if not (isinstance(quantity, Decimal) and quantity > Decimal("0")):
            raise ValueError("Order quantity must be a positive Decimal.")
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("Limit orders require a price.")
        
        self._type = EventType.ORDER
        self.order_id = order_id
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.quantity = quantity
        self.order_type = order_type
        self.price = price

    @property
    def type(self) -> EventType:
        return self._type

    def __repr__(self):
        return (f"OrderEvent(order_id='{self.order_id}', symbol='{self.symbol}', direction='{self.direction}', "
                f"quantity={self.quantity}, type='{self.order_type}', price={self.price}, "
                f"timestamp={self.timestamp.date()})")
    
class FillEvent(Event):
    """
    Encapsulates the notion of an order being filled, with a quantity and an actual fill prices.
    Comes from the execution handler.
    """
    def __init__(
        self,
        order_id: str,
        symbol: str,
        timestamp: datetime,
        direction: Signal,
        quantity: Decimal,
        fill_price: Decimal,
        commission: Decimal = Decimal('0.0'),
        successful: bool = True 
    ):
        if not (isinstance(quantity, Decimal) and quantity > Decimal('0')):
            raise ValueError("Fill quantity must be a positive Decimal.")
        if not (isinstance(fill_price, Decimal) and fill_price > Decimal('0')):
            raise ValueError("Fill price must be a positive Decimal.")

        self._type = EventType.FILL
        self.order_id = order_id
        self.symbol = symbol
        self.timestamp = timestamp
        self.direction = direction
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.successful = successful

    @property
    def type(self) -> EventType:
        return self._type

    def __repr__(self):
        return (f"FillEvent(order_id='{self.order_id}', symbol='{self.symbol}', direction='{self.direction}', "
                f"quantity={self.quantity}, fill_price={self.fill_price}, commission={self.commission}, "
                f"successful={self.successful}, timestamp={self.timestamp.date()})")
    
class DailyUpdateEvent:
    """
    Represents an event signifying the end of a trading day, 
    triggering daily portfolio value calculations and updates.
    """
    def __init__(self, timestamp: datetime):
        self._type = EventType.DAILY_UPDATE
        self.timestamp = timestamp

    @property
    def type(self) -> EventType:
        return self._type
    
    def __repr__(self):
        return f"DailyUpdateEvent(timestamp={self.timestamp.date()})"