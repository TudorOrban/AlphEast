from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar


class PriceBarClient(ABC):
    @abstractmethod
    def get_price_bar_data(
        self,
        symbol: str,
        start_date: datetime, 
        end_date: datetime, 
        interval: Interval
    ) -> List[PriceBar]:
        """
        Abstract method to fetch price bar data for a given symbol, date range and interval.
        """
        pass