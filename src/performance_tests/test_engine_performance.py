import cProfile
from datetime import datetime
import time as time_module 
import io
import logging
import os
import pstats
from typing import List
from memory_profiler import profile as mem_profile

from alpheast.config.backtest_config import BacktestingOptions
from alpheast.config.data_source import DataSource, DataSourceType
from alpheast.engine import BacktestingEngine
from alpheast.models.interval import Interval
from alpheast.position_sizing.common.fixed_allocation_sizing import FixedAllocationSizing
from alpheast.strategy.common.sma_crossover_strategy import SMACrossoverStrategy
from performance_tests.database.repository import PriceDataRepository

# @mem_profile
def run_backtest_scenario(
    scenario_name: str,
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    interval: Interval,
    initial_cash: float = 100_000.0,
    transaction_cost_percent: float = 0.001,
    slippage_percent: float = 0.0005,
    position_sizing_value: float = 0.5
):
    print(f"\n--- Running Scenario: {scenario_name} ---")
    print(f"  Symbols: {len(symbols)}, From: {start_date.date()}, To: {end_date.date()}, Interval: {interval.name}")

    logging.disable(logging.CRITICAL) 

    repository = PriceDataRepository()
    price_bar_data = repository.get_multiple_symbols_data(symbols, start_date, end_date, interval)
    
    options = BacktestingOptions(
        symbols=symbols,
        start_date=start_date.date(),
        end_date=end_date.date(),
        interval=interval,
        initial_cash=initial_cash,
        transaction_cost_percent=transaction_cost_percent,
        slippage_percent=slippage_percent
    )

    data_source = DataSource(
        type=DataSourceType.DIRECT,
        price_bar_data=price_bar_data,
    )

    engine = BacktestingEngine(
        options=options,
        data_source=data_source,
        strategies=[SMACrossoverStrategy(symbol=symbol) for symbol in symbols],
        position_sizing_method=FixedAllocationSizing(position_sizing_value)
    )

    start_time = time_module.time()
    results = engine.run()
    end_time = time_module.time()

    elapsed_time = end_time - start_time
    print(f"  Scenario '{scenario_name}' completed in {elapsed_time:.4f} seconds.")
    
    logging.disable(logging.NOTSET) 
    
    return elapsed_time, results

if __name__ == "__main__":
    scenarios = {
        "1_Symbol_1_Year": {
            "symbols": ["AAPL"],
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
        "2_Symbols_1_Year": {
            "symbols": ["AAPL", "MSFT"],
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
        "10_Symbols_1_Year": {
            "symbols": ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOG", "META", "TSM", "WMT", "JPM"],
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
        "1_Symbol_5_Years": {
            "symbols": ["AAPL"],
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
        "2_Symbols_5_Years": {
            "symbols": ["AAPL", "MSFT"],
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
        "10_Symbols_5_Years": {
            "symbols": ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOG", "META", "TSM", "WMT", "JPM"],
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2025, 1, 1),
            "interval": Interval.DAILY
        },
    }

    overall_results = {}

    for name, config in scenarios.items():
        print(f"\n--- Starting cProfile for {name} ---")
        pr = cProfile.Profile()
        pr.enable()

        elapsed_time, _ = run_backtest_scenario(
            scenario_name=name,
            symbols=config["symbols"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            interval=config["interval"]
        )

        pr.disable()
        overall_results[name] = {"time": elapsed_time}

        s = io.StringIO()
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats(".*")

        current_dir = os.path.dirname(__file__)
        profile_output_path = os.path.join(current_dir, f"results/{name}_cprofile_results.txt")
        with open(profile_output_path, "w+") as f:
            f.write(s.getvalue())
        print(f"  cProfile results saved to: {profile_output_path}")

    print("\n--- All Scenarios Finished ---")
    print("\nSummary of Execution Times:")
    for name, metrics in overall_results.items():
        print(f"- {name}: {metrics["time"]:.4f} seconds")

    print("\nTo run memory profiling for a specific scenario:")
    print("1. Comment out `cProfile` block for that scenario in this script.")
    print("2. Run from your terminal: `python -m memory_profiler performance_tests/test_performance_engine.py`")
    print("   Look for lines starting with 'MiB' in the output for memory usage.")