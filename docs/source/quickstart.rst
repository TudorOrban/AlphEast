Quick Start
============
This guide will get you up and running with AlphEast in minutes.

Installation
------------
You can easily install AlphEast using pip:

.. code-block:: bash

    pip install alpheast

Understanding the Engine's Core Components
------------------------------------------
To run the :py:class:`~alpheast.engine.BacktestingEngine`, you need to provide it with four key components:

1.  **Backtesting Options**: A :py:class:`~alpheast.config.backtest_config.BacktestingOptions` object specifies core parameters like financial **symbols**, **start and end dates**, **bar interval**, and **initial capital**.
2.  **Data Source**: This defines how the engine gets its historical price data. Data can be provided in three ways:

    :Directly: Set the ``price_bar_data`` property of the :py:class:`~alpheast.config.data_source.DataSource` directly with your own pre-loaded data (a :py:class:`~alpheast.models.price_bar.PriceBar` list).
    :Custom Client: Implement a custom :py:class:`~alpheast.data.clients.base.PriceBarClient` that fetches data from your preferred data source.
    :Standard Client: Use a predefined client implementation (currently, only Alpha Vantage is supported) by providing an API key.
    
3.  **Trading Strategy**: An object that implements the :py:class:`~alpheast.strategy.base.BaseStrategy` interface. You can use one of the predefined strategies found in :py:mod:`alpheast.strategy.common` or create your own.
4.  **Position Sizing Method**: An object that implements the :py:class:`~alpheast.position_sizing.base.BasePositionSizing` interface. Similar to strategies, you can use a predefined method from :py:mod:`alpheast.position_sizing.common` or define a custom one.

---

Basic Usage Example
-------------------
Here's a basic example demonstrating how to set up and run a simple backtest with AlphEast:

.. code-block:: python

    from datetime import datetime
    from typing import Dict, List
    from alpheast.config.data_source import DataSource, DataSourceType
    from alpheast.engine import BacktestingEngine
    from alpheast.config.backtest_config import BacktestingOptions
    from alpheast.models.interval import Interval
    from alpheast.models.price_bar import PriceBar
    from alpheast.strategy.common.sma_crossover_strategy import SMACrossoverStrategy
    from alpheast.position_sizing.common.fixed_allocation_sizing import FixedAllocationSizing


    symbol = "AAPL"
    options = BacktestingOptions(
        symbols=[symbol],
        start_date=datetime(2021, 1, 1),
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