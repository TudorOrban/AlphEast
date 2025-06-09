from enum import Enum


class EventType(Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"
    DAILY_UPDATE = "DAILY_UPDATE"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"