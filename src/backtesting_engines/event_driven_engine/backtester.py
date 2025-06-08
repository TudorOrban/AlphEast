from datetime import date
from decimal import Decimal
import logging
from typing import Any, Dict, List

from src.data.price_bars.interval import Interval
from src.shared.metrics import calculate_performance_metrics
from src.shared.plotting import PerformancePlotter
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.handlers.database_data_handler import DatabaseDataHandler
from src.backtesting_engines.event_driven_engine.handlers.simulated_execution_handler import SimulatedExecutionHandler
from src.backtesting_engines.event_driven_engine.models.input_data import PriceBar
from src.backtesting_engines.event_driven_engine.portfolio.portfolio_manager import PortfolioManager
from src.backtesting_engines.event_driven_engine.position_sizing.examples.fixed_allocation_sizing import FixedAllocationSizing
from src.backtesting_engines.event_driven_engine.strategy.base_strategy import NewBaseStrategy
from src.backtesting_engines.event_driven_engine.strategy.examples.sma_crossover_strategy import SMACrossoverStrategy

class EventDrivenBacktester:
    """
    Orchestrates the event-driven backtesting process.
    Initializes all components and runs the main event loop.
    """
    def __init__(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: Interval = Interval.DAILY,
        initial_cash: float = 100000.0,
        fast_period: int = 10,
        slow_period: int = 50,
        transaction_cost_percent: float = 0.001,
        price_data: Dict[str, List[PriceBar]] = {}
    ):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.initial_cash = initial_cash

        decimal_transaction_cost = Decimal(str(transaction_cost_percent))

        self.event_queue = EventQueue()

        self.data_handler = DatabaseDataHandler(
            event_queue=self.event_queue,
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval,
            price_data=price_data
        )

        self.strategies: List[NewBaseStrategy] = []
        for symbol in self.symbols:
            strategy = SMACrossoverStrategy(
                event_queue=self.event_queue,
                symbol=symbol,
                fast_period=fast_period,
                slow_period=slow_period
            )
            self.strategies.append(strategy)

        position_sizing_method = FixedAllocationSizing(0.5)
        self.portfolio_manager = PortfolioManager(
            event_queue=self.event_queue,
            initial_cash=self.initial_cash,
            transaction_cost_percent=decimal_transaction_cost,
            position_sizing_method=position_sizing_method,
            symbols=self.symbols
        )

        self.execution_handler = SimulatedExecutionHandler(
            event_queue=self.event_queue,
            transaction_cost_percent=decimal_transaction_cost
        )

        self.plotter = PerformancePlotter()

        logging.info("New Backtester initialized")

    def run(self):
        """
        Runs the main event loop of the backtesting engine
        """
        logging.info(f"Starting Backtest for {self.symbols} from {self.start_date} to {self.end_date}")

        while self.data_handler.continue_backtest() or not self.event_queue.empty():
            # --- 1. Push next MarketEvents for the current interval ---
            if self.data_handler.continue_backtest():
                self.data_handler.stream_next_market_event()

            # --- 2. Process all events currently in the queue ---
            while not self.event_queue.empty():
                self._process_next_event()

        # -- Post-Backtest Analysis ---
        daily_values = self.portfolio_manager.get_daily_values()
        benchmark_daily_values = self.portfolio_manager.get_benchmark_daily_values()
        trade_log = self.portfolio_manager.get_trade_log()
        final_portfolio_summary = self.portfolio_manager.get_summary()

        if not daily_values:
            logging.error("No daily values recorded, skipping Summary.")
            return

        performance_metrics = calculate_performance_metrics(
            daily_values=daily_values,
            trade_log=trade_log,
            benchmark_daily_values=benchmark_daily_values
        )

        self._print_metrics(
            final_portfolio_summary, 
            trade_log, 
            performance_metrics
        )

        plot_title = f"Event-Driven Portfolio Equity Curve: Multiple Symbols with SMA Crossover"
        self.plotter.plot_equity_curve(
            daily_values=daily_values,
            benchmark_daily_values=benchmark_daily_values, 
            title=plot_title
        )

        return {
            "performance_metrics": performance_metrics,
            "daily_values": daily_values,
            "benchmark_daily_values": benchmark_daily_values,
            "trade_log": trade_log,
            "final_portfolio_summary": final_portfolio_summary
        }

    def _process_next_event(self):
        event = self.event_queue.get()

        if event is None:
            return

        logging.debug(f"Processing event: {event}")

        if event.type == "MARKET":
            for strategy in self.strategies:
                strategy.on_market_event(event)
                
            self.portfolio_manager.on_market_event(event)
            self.execution_handler.on_market_event(event)

        elif event.type == "SIGNAL":
            self.portfolio_manager.on_signal_event(event)

        elif event.type == "ORDER":
            self.execution_handler.on_order_event(event)

        elif event.type == "FILL":
            self.portfolio_manager.on_fill_event(event)

        elif event.type == "DAILY_UPDATE":
            self.portfolio_manager.on_daily_update_event(event)

        else:
            logging.warning(f"Unknown event type received: {event.type}")

    def _print_metrics(
        self,
        final_portfolio_summary: Dict[str, Any],
        trade_log: List[Dict[str, Any]],
        performance_metrics: Dict[str, Any]
    ):
        print("\n--- Event-Driven Backtest Summary ---")
        print(f"Initial Cash: ${self.initial_cash:.2f}")
        print(f"Final Cash: ${final_portfolio_summary["cash"]:.2f}")
        print(f"Final Holdings: {final_portfolio_summary["holdings"]}")
        print(f"Total Trades: {len(trade_log)}")
        
        # Print Strategy Performance
        if "strategy" in performance_metrics and "error" not in performance_metrics["strategy"]:
            print("\n--- Performance Metrics (Strategy) ---")
            for metric, value in performance_metrics["strategy"].items():
                print(f"{metric.replace('_', ' ').title()}: {value}")
        elif "strategy" in performance_metrics and "error" in performance_metrics["strategy"]:
            print(f"\n--- Strategy Performance Error ---")
            print(performance_metrics['strategy']['error'])

        # Print Benchmark Performance
        if "benchmark" in performance_metrics and "error" not in performance_metrics["benchmark"]:
            print("\n--- Performance Metrics (Benchmark) ---")
            for metric, value in performance_metrics["benchmark"].items():
                print(f"{metric.replace('_', ' ').title()}: {value}")
        elif "benchmark" in performance_metrics and "error" in performance_metrics["benchmark"]:
            print(f"\n--- Benchmark Performance Error ---")
            print(performance_metrics['benchmark']['error'])

        print("-----------------------------------")
        