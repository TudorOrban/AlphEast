from datetime import datetime
import logging
from src.data.eod_prices.repository import EODPriceRepository
from src.data.sources.alpha_vantage_client import AlphaVantageClient


class FinancialDataService:
    def __init__(self, alpha_vantage_api_key: str):
        self.alpha_vantage_client = AlphaVantageClient(api_key=alpha_vantage_api_key)
        self.eod_repository = EODPriceRepository()

    def fetch_and_save_eod_prices(self, symbol: str, start_date: datetime, end_date: datetime):
        raw_eod_data = self.alpha_vantage_client.get_eod_prices(symbol, start_date, end_date)

        if not raw_eod_data:
            logging.warning(f"No EOD data retrieved for {symbol}. Nothing to save.")
            return
        
        try:
            self.eod_repository.save_eod_prices(raw_eod_data)
            logging.info(f"Completed fetch and save process for {symbol}.")
        except Exception as e:
            logging.error(f"Failed to save EOD prices for {symbol}: {e}")