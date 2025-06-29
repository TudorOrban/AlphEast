
from datetime import datetime
from typing import Dict, List
from alpheast.config.data_source import DataSource, DataSourceType
from alpheast.engine import BacktestingEngine
from alpheast.config.backtest_config import BacktestingOptions
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar
from alpheast.position_sizing.common.fixed_allocation_sizing import FixedAllocationSizing
from alpheast.strategy.common.sma_crossover_strategy import SMACrossoverStrategy


if __name__ == "__main__":
    symbol = "AAPL"
    options = BacktestingOptions(
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
        options=options,
        data_source=data_source,
        strategies=[SMACrossoverStrategy(symbol)],
        position_sizing_method=FixedAllocationSizing(0.5)
    )
    
    results = engine.run()

    if results:
        results.print_summary()
        results.plot_equity_curve()