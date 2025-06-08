from datetime import datetime
from decimal import Decimal
import logging
import requests
from typing import Any, Dict, List, Optional
from src.data.sources.financial_data_client import FinancialDataClient


class AlphaVantageClient(FinancialDataClient):
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Alpha Vantage API key cannot be empty.")
        self.api_key = api_key
        logging.info("AlphaVantage Client initialized")

    def get_eod_prices(self, symbol, start_date, end_date) -> List[Dict[str, Any]]:
        logging.info(f"Fetching EOD prices for {symbol} from Alpha Vantage...")
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full"
        }
        data = self._make_request(params)

        if not data or "Time Series (Daily)" not in data:
            logging.error(f"Couldd not retrieve daily time series data for {symbol}")
            return []

        eod_prices: List[Dict[str, Any]] = []
        time_series = data["Time Series (Daily)"]

        for date_str, values in time_series.items():
            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if start_date.date() <= current_date <= end_date.date():
                try:
                    eod_prices.append({
                        "time": datetime.combine(current_date, datetime.min.time()),
                        "symbol": symbol,
                        "open": Decimal(values["1. open"]),
                        "high": Decimal(values["2. high"]),
                        "low": Decimal(values["3. low"]),
                        "close": Decimal(values["4. close"]),
                        "volume": int(values["5. volume"])
                    })
                except KeyError as ke:
                    logging.warning(f"Missing key in Alpha Vantage data for {symbol} on {date_str}: {ke}")
                except ValueError as ve:
                    logging.warning(f"Value conversion error for {symbol} on {date_str}: {ve}")

        eod_prices.sort(key=lambda x: x["time"])
        logging.info(f"Retrieved {len(eod_prices)} EOD prices for {symbol} within specified data range.")
        return eod_prices

    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        params["apikey"] = self.api_key

        try:
            response = requests.get(self.BASE_URL, params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                logging.error(f"Alpha Vantage API Error: {data["Error Message"]}")
                return None
            if "Note" in data:
                logging.warning(f"Alpha Vantage API Note: {data["Note"]}")
            return data
        except requests.exceptions.HTTPError as http_error:
            logging.error(f"HTTP error occurred: {http_error}")
        return None