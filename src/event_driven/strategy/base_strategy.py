
from abc import ABC

from src.event_driven.event_queue import EventQueue


class NewBaseStrategy(ABC):
    """
    Abstract base class for the trading strategy in the new event-driven backtesting engine.
    Strategies process MarketEvents and generate SignalEvents.
    """
    # def __init__(self, event_queue: EventQueue, symbol)