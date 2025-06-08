
import queue
from typing import Optional

from src.event_driven.models.event import Event


class EventQueue:
    """
    A synchronized queue for managing events in the event-driven backtesting system.
    """
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, event: Event):
        self._queue.put(event)

    def get(self) -> Optional[Event]:
        try:
            return self._queue.get(block=False)
        except queue.Empty:
            return None
        
    def empty(self) -> bool:
        return self._queue.empty()