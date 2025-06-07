from abc import ABC, abstractmethod
from datetime import datetime


class FinancialDataClient(ABC):
    @abstractmethod
    def get_eod_prices(self, symbol: str, start_date: datetime, end_date: datetime):
        """
        Fetches End-Of-Day (EOD) prices for a given symbol within a date range.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL").
            start_date (date): The start date for the data (inclusive).
            end_date (date): The end date for the data (inclusive).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                   represents an EOD price record. The keys should
                                   ideally match the EODPrice model's column names
                                   (time, symbol, open, high, low, close, volume).
                                   The 'time' key should be a datetime object.
        """
        pass