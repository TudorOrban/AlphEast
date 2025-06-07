from datetime import datetime
from config import ALPHA_VANTAGE_API_KEY
from src.data.eod_prices.service import FinancialDataService
from src.data.sources.alpha_vantage_client import AlphaVantageClient

eod_price_service = FinancialDataService(ALPHA_VANTAGE_API_KEY)

eod_price_service.fetch_and_save_eod_prices("AAPL", start_date=datetime(2025, 1, 28, 23, 55, 59, 342380), end_date=datetime.now())