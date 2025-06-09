from datetime import datetime
import logging
from alpheast.models.interval import Interval
from examples.full.clients.alpha_vantage_price_bar_client import AlphaVantagePriceBarClient
from examples.full.database.repository import PriceDataRepository 

class FinancialDataService:
    def __init__(self, alpha_vantage_api_key: str):
        self.alpha_vantage_client = AlphaVantagePriceBarClient(api_key=alpha_vantage_api_key)
        self.price_data_repository = PriceDataRepository()
        
    def fetch_and_save_price_data(self, symbol: str, start_date: datetime, end_date: datetime, interval: Interval):
        """
        Fetches price data for a given symbol and interval from Alpha Vantage
        and saves it to the database.
        """
        raw_price_data = self.alpha_vantage_client.get_price_bar_data(symbol, start_date, end_date, interval)

        if not raw_price_data:
            logging.warning(f"No {interval.value} data retrieved for {symbol}. Nothing to save.")
            return
        
        try:
            self.price_data_repository.save_price_bars(raw_price_data)
            logging.info(f"Completed fetch and save process for {symbol} ({interval.value}).")
        except Exception as e:
            logging.error(f"Failed to save {interval.value} prices for {symbol}: {e}")