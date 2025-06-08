from datetime import datetime
import logging
from src.backtesting_engine.backtester import Backtester
from src.strategy.examples.basic_strategy import BasicStrategy

try:
    my_strategy = BasicStrategy("AAPL")

    backtester = Backtester(strategy=my_strategy, initial_cash=100000.0)

    backtest_start_date = datetime(2025, 1, 29)
    backtest_end_date = datetime(2025, 5, 29)

    backtest_results = backtester.run(
        symbol="AAPL",
        start_date=backtest_start_date,
        end_date=backtest_end_date
    )

except Exception as e:
    logging.critical(f"An unhandled error occurred in main: {e}", exc_info=True)