
from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

import requests
from alpheast.data.price_bar_client import PriceBarClient
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar


class AlphaVantageStdPriceBarClient(PriceBarClient):
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

    def get_price_bar_data(
        self,
        symbol: str,
        start_date: datetime, 
        end_date: datetime, 
        interval: Interval
    ) -> List[PriceBar]:
        logging.info(f"Fetching price bar data for {symbol} from Alpha Vantage...")
        
        function = self._FUNCTION_MAP.get(interval)
        if not function:
            logging.error(f"Unsupported interval for Alpha Vantage: {interval.value}")
            return []
        
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full"
        }

        if interval in self._INTRADAY_INTERVAL_PARAM_MAP:
            params["interval"] = self._INTRADAY_INTERVAL_PARAM_MAP[interval]
            time_series_key = f"Time Series ({params['interval']})"
        else:
            time_series_key = "Time Series (Daily)"

        data = self._make_request(params)

        if not data or time_series_key not in data:
            logging.error(f"Could not retrieve {interval.value} time series data for {symbol}. Raw data: {data}")
            return []

        price_bar_data: List[PriceBar] = []
        time_series = data[time_series_key]

        for date_str, values in time_series.items():
            current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S") if " " in date_str else datetime.strptime(date_str, "%Y-%m-%d")

            if start_date <= current_date.date() <= end_date:
                try:
                    price_bar_data.append(PriceBar(
                        timestamp=datetime.combine(current_date, datetime.min.time()),
                        symbol=symbol,
                        open=Decimal(values["1. open"]),
                        high=Decimal(values["2. high"]),
                        low=Decimal(values["3. low"]),
                        close=Decimal(values["4. close"]),
                        volume=int(values["5. volume"])
                    ))
                except KeyError as ke:
                    logging.warning(f"Missing key in Alpha Vantage data for {symbol} on {date_str}: {ke}")
                except ValueError as ve:
                    logging.warning(f"Value conversion error for {symbol} on {date_str}: {ve}")

        price_bar_data.sort(key=lambda x: x.timestamp)
        logging.info(f"Retrieved {len(price_bar_data)} EOD prices for {symbol} within specified data range.")
        return price_bar_data
    

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
        except requests.exceptions.ConnectionError as conn_error:
            logging.error(f"Connection error occurred while fetching from Alpha Vantage: {conn_error}. Request params: {params}")
        except requests.exceptions.Timeout as timeout_error:
            logging.error(f"Timeout occurred while fetching from Alpha Vantage: {timeout_error}. Request params: {params}")
        except ValueError:
            logging.error(f"Could not decode JSON response from Alpha Vantage. Response: {response.text}. Request params: {params}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during Alpha Vantage request: {e}. Request params: {params}")
        return None