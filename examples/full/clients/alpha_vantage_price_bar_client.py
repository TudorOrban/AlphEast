
import logging
from alpheast.data.price_bar_client import PriceBarClient
from alpheast.models.interval import Interval


class AlphaVantagePriceBarClient(PriceBarClient):
    BASE_URL = "https://www.alphavantage.co/query"
    
    _FUNCTION_MAP = {
        Interval.DAILY: "TIME_SERIES_DAILY",
        Interval.HOURLY: "TIME_SERIES_INTRADAY",
        Interval.MINUTE_30: "TIME_SERIES_INTRADAY",
    }
    _INTRADAY_INTERVAL_PARAM_MAP = {
        Interval.HOURLY: "60min",
        Interval.MINUTE_30: "30min",
    }

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Alpha Vantage API key cannot be empty.")
        self.api_key = api_key
        logging.info("AlphaVantage Client initialized")
