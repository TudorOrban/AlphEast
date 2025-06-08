from datetime import datetime
import logging
from typing import Dict, List
from config import ALPHA_VANTAGE_API_KEY
from src.data.price_bars.repository import PriceDataRepository
from src.data.price_bars.service import FinancialDataService
from src.data.price_bars.interval import Interval
from src.backtesting_engines.event_driven_engine.models.input_data import PriceBar
from src.backtesting_engines.event_driven_engine.backtester import EventDrivenBacktester


def run_backtest(
    symbols: List[str], 
    start_date: datetime, 
    end_date: datetime,
    interval: Interval,
    price_data: Dict[str, List[PriceBar]]
):
    logging.info("--- Running Standard Backtester ---")
    engine = EventDrivenBacktester(
        symbols=symbols,
        start_date=start_date.date(),
        end_date=end_date.date(),
        interval=interval,
        initial_cash=100000.0,
        fast_period=10,
        slow_period=50,
        transaction_cost_percent=0.001,
        price_data=price_data
    )
    engine.run()
    logging.info("--- Standard Backtester Finished ---")


if __name__ == "__main__":
    SYMBOLS = ["AAPL", "MSFT"]
    START_DATE = datetime(2020, 1, 1)
    END_DATE = datetime(2025, 1, 1)
    INTERVAL = Interval.DAILY

    # service = FinancialDataService(ALPHA_VANTAGE_API_KEY)
    # service.fetch_and_save_price_data("MSFT", START_DATE, END_DATE, INTERVAL)

    repository = PriceDataRepository()

    price_data: Dict[str, List[PriceBar]] = {}
    for symbol in SYMBOLS:
        price_bars: List[PriceBar] = repository.get_price_data(
            symbol=symbol,
            start_date=START_DATE,
            end_date=END_DATE,
            interval=INTERVAL
        )
        price_data[symbol] = price_bars

    run_backtest(SYMBOLS, START_DATE, END_DATE, INTERVAL, price_data)