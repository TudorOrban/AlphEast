from datetime import datetime
from alpheast.config.data_source import DataSource, DataSourceType
from alpheast.models.interval import Interval
from alpheast.engine import BacktestingEngine
from alpheast.config.backtest_config import BacktestingOptions
from examples.full.database.repository import PriceDataRepository
from examples.full.strategies.example_strategy import ExampleStrategy
from examples.full.strategies.example_position_sizing import ExamplePositionSizing


if __name__ == "__main__":
    SYMBOLS = ["AAPL", "MSFT"]
    INITIAL_CASH = 100_000.0
    START_DATE = datetime(2022, 1, 1)
    END_DATE = datetime(2025, 1, 1)
    INTERVAL = Interval.DAILY
    TRANSACTION_COST_PERCENT = 0.001
    SLIPPAGE_PERCENT = 0.0005
    POSITION_SIZING = 0.5

    repository = PriceDataRepository()
    price_bar_data = repository.get_multiple_symbols_data(SYMBOLS, START_DATE, END_DATE, INTERVAL)
    
    options = BacktestingOptions(
        symbols=SYMBOLS,
        start_date=START_DATE.date(),
        end_date=END_DATE.date(),
        interval=INTERVAL,
        initial_cash=INITIAL_CASH,
        transaction_cost_percent=TRANSACTION_COST_PERCENT,
        slippage_percent=SLIPPAGE_PERCENT
    )

    data_source = DataSource(
        type=DataSourceType.DIRECT,
        price_bar_data=price_bar_data,
    )

    engine = BacktestingEngine(
        options=options,
        data_source=data_source,
        strategies=[ExampleStrategy(symbol=symbol) for symbol in SYMBOLS],
        position_sizing_method=ExamplePositionSizing(POSITION_SIZING)
    )
    
    results = engine.run()

    if results:
        results.print_summary()
        results.plot_equity_curve()