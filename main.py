from datetime import datetime
import logging
from typing import List
from config import ALPHA_VANTAGE_API_KEY
from src.data.interval import Interval
from src.backtesting_engines.simple_engine.strategy.examples.basic_strategy import BasicStrategy
from src.backtesting_engines.event_driven_engine.backtester import EventDrivenBacktester
from src.data.eod_prices.service import FinancialDataService
from src.backtesting_engines.simple_engine.backtester import SimpleBacktester


def run_old_backtest(symbol: str, start_date: datetime, end_date: datetime):
    logging.info("--- Running Old (Bar-by-Bar) Backtesting Engine")

    strategy = BasicStrategy(symbol)
    backtester = SimpleBacktester(strategy=strategy, initial_cash=100000.0)
    backtester.run(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )

    logging.info("--- Old Backtest Finished ---")

def run_new_backtest(
    symbols: List[str], 
    start_date: datetime, 
    end_date: datetime,
    interval: Interval
):
    logging.info("--- Running New (Event-Driven) Backtester ---")
    engine = EventDrivenBacktester(
        symbols=symbols,
        start_date=start_date.date(),
        end_date=end_date.date(),
        interval=interval,
        initial_cash=100000.0,
        fast_period=10,
        slow_period=50,
        transaction_cost_percent=0.001
    )
    engine.run()
    logging.info("--- New Event-Driven Backtest Finished ---")


if __name__ == "__main__":
    SYMBOLS = ["AAPL", "MSFT"]
    START_DATE = datetime(2020, 1, 1)
    END_DATE = datetime(2025, 1, 1)
    
    # service = FinancialDataService(ALPHA_VANTAGE_API_KEY)
    # service.fetch_and_save_eod_prices("AAPL", START_DATE, END_DATE)

    run_new_backtest(SYMBOLS, START_DATE, END_DATE, Interval.DAILY)