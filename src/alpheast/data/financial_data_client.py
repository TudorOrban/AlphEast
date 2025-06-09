from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from alpheast.models.interval import Interval


class FinancialDataClient(ABC):
    @abstractmethod
    def get_price_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime, 
        interval: Interval
    ) -> List[Dict[str, Any]]:
        """
        Abstract method to fetch price data for a given symbol, date range, and interval.
        Returns a list of dictionaries, each convertible to a PriceBar.
        """
        pass
