from datetime import datetime
import logging
from config import ALPHA_VANTAGE_API_KEY
from src.data.eod_prices.service import FinancialDataService
from src.backtesting_engine.backtester import Backtester
from src.strategy.examples.basic_strategy import BasicStrategy

symbol = "MSFT"

try:
    # service = FinancialDataService(alpha_vantage_api_key=ALPHA_VANTAGE_API_KEY)
    # service.fetch_and_save_eod_prices(symbol, datetime(2020, 1, 1), datetime(2025, 1, 1))

    my_strategy = BasicStrategy(symbol)

    backtester = Backtester(strategy=my_strategy, initial_cash=100000.0)

    backtest_start_date = datetime(2022, 1, 1)
    backtest_end_date = datetime(2025, 1, 1)

    backtest_results = backtester.run(
        symbol=symbol,
        start_date=backtest_start_date,
        end_date=backtest_end_date
    )
except Exception as e:
    logging.critical(f"An unhandled error occurred in main: {e}", exc_info=True)