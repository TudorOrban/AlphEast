
from datetime import datetime
from typing import Dict, List
from alpheast.config.data_source import DataSource, DataSourceType
from alpheast.engine import BacktestingEngine
from alpheast.config.backtest_config import BacktestConfig
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar
from examples.basic.example_strategy import ExampleStrategy


if __name__ == "__main__":
    symbol = "AAPL"
    config = BacktestConfig(
        symbols=[symbol],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2025, 1, 1),
        interval=Interval.DAILY,
        initial_cash=100_000.0
    )

    price_bar_data: Dict[str, List[PriceBar]] = {
        symbol: [] # Provide your data
    }
    data_source = DataSource(
        type=DataSourceType.DIRECT,
        price_bar_data=price_bar_data,
    )

    engine = BacktestingEngine(
        config=config,
        data_source=data_source,
        strategies=[ExampleStrategy(symbol)],
    )
    
    results = engine.run()

    if results:
        results.print_summary()
        results.plot_equity_curve()

    