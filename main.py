from datetime import datetime
from typing import Dict, List
from config import ALPHA_VANTAGE_API_KEY
from src.data.price_bars.repository import PriceDataRepository
from src.data.price_bars.service import FinancialDataService
from src.data.price_bars.interval import Interval
from src.backtesting_engines.event_driven_engine.models.input_data import PriceBar
from src.backtesting_engines.event_driven_engine.backtester import BacktestingEngine
from src.backtesting_engines.event_driven_engine.backtest_config import BacktestConfig
from src.examples.example_strategy import ExampleStrategy
from src.examples.example_position_sizing import ExamplePositionSizing

if __name__ == "__main__":
    SYMBOLS = ["AAPL", "MSFT"]
    INITIAL_CASH = 100_000.0
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


    config = BacktestConfig(
        symbols=SYMBOLS,
        start_date=START_DATE.date(),
        end_date=END_DATE.date(),
        interval=INTERVAL,
        initial_cash=INITIAL_CASH,
        transaction_cost_percent=0.001,
        slippage_percent=0.0005
    )

    example_strategy_aapl = ExampleStrategy(symbol="AAPL")
    example_strategy_msft = ExampleStrategy(symbol="MSFT")
    example_position_sizing = ExamplePositionSizing(0.5)

    engine = BacktestingEngine(
        config=config,
        price_data=price_data,
        data_client=None,
        strategies=[example_strategy_aapl, example_strategy_msft],
        position_sizing_method=example_position_sizing
    )
    engine.run()