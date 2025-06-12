from decimal import Decimal
import logging
import os
from typing import List, Optional

from alpheast.config.config_loader import ConfigLoader
from alpheast.config.data_source import DataSource
from alpheast.models.backtest_results import BacktestResults
from alpheast.events.event_queue import EventQueue
from alpheast.handlers.data_handler import DataHandler
from alpheast.handlers.simulated_execution_handler import SimulatedExecutionHandler
from alpheast.config.backtest_config import BacktestingOptions
from alpheast.events.event_enums import EventType
from alpheast.portfolio.portfolio_manager import PortfolioManager
from alpheast.shared.utils.project_root_finder import find_project_root
from alpheast.strategy.base_strategy import BaseStrategy
from alpheast.position_sizing.base_position_sizing import BasePositionSizing
from alpheast.shared.metrics import calculate_performance_metrics

class BacktestingEngine:
    """
    Orchestrates the event-driven backtesting process.
    Initializes all main components:
    EventQueue, DataHandler, Strategies, PortfolioManager, SimulatedExecutionHandler 
    and runs the main event loop.
    """
    def __init__(
        self,
        options: BacktestingOptions,
        data_source: DataSource,
        strategies: List[BaseStrategy],
        position_sizing_method: Optional[BasePositionSizing] = None
    ):
        self._initialize_config(options)
        self.event_queue = EventQueue()

        self.data_handler = DataHandler(
            event_queue=self.event_queue,
            symbols=self.config.symbols,
            start_date=self.config.start_date,
            end_date=self.config.end_date,    
            interval=self.config.interval,
            data_source=data_source
        )

        self.strategies: List[BaseStrategy] = []
        for strategy_instance in strategies:
            strategy_instance.set_event_queue(self.event_queue)
            self.strategies.append(strategy_instance)
        
        decimal_transaction_cost = Decimal(str(self.config.transaction_cost_percent))
        decimal_slippage_percent = Decimal(str(self.config.slippage_percent))

        self.portfolio_manager = PortfolioManager(
            event_queue=self.event_queue,
            symbols=self.config.symbols,
            initial_cash=self.config.initial_cash,
            transaction_cost_percent=decimal_transaction_cost,
            slippage_percent=decimal_slippage_percent,
            position_sizing_method=position_sizing_method
        )

        self.execution_handler = SimulatedExecutionHandler(
            event_queue=self.event_queue,
            transaction_cost_percent=decimal_transaction_cost,
            slippage_percent=decimal_slippage_percent
        )

        logging.info("Backtesting Engine initialized.")
        
    def _initialize_config(self, options: BacktestingOptions):
        """
        Initializes the backtest config by the following rules:
        - if an alpheast_config.json is not present in project root, use passed options
        - otherwise, load the json into a BacktestingOptions and override with any passed option values
        In both cases, perform validation at the end. 
        """
        is_json_loaded = False

        project_root = find_project_root()
        json_file_path = os.path.join(project_root, "alpheast_config.json") if project_root is not None else None

        if json_file_path is not None and os.path.exists(json_file_path):
            try:
                backtest_options = ConfigLoader.load_backtest_config_from_json(json_file_path)
                is_json_loaded = True
            except Exception as e:
                logging.warning(f"Failed to load alpheast_config.json: {e}")

        if is_json_loaded:
            backtest_options.override(options)
            self.config = backtest_options.validate()
        else:
            self.config = options.validate()

        self.config.log()

    def run(self) -> Optional[BacktestResults]:
        """
        Runs the main event loop of the backtesting engine
        """
        logging.info(f"Starting Backtest for {self.config.symbols} from {self.config.start_date} to {self.config.end_date}")

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
            raise Exception("Failed: No daily values.")

        performance_metrics = calculate_performance_metrics(
            daily_values=daily_values,
            trade_log=trade_log,
            benchmark_daily_values=benchmark_daily_values
        )

        results = BacktestResults(
            performance_metrics=performance_metrics,
            daily_values=daily_values,
            benchmark_daily_values=benchmark_daily_values,
            trade_log=trade_log,
            final_portfolio_summary=final_portfolio_summary,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_cash=self.config.initial_cash
        )

        logging.info("--- Backtest Finished ---")
        return results

    def _process_next_event(self):
        event = self.event_queue.get()

        if event is None:
            return

        logging.debug(f"Processing event: {event}")

        if event.type == EventType.MARKET:
            for strategy in self.strategies:
                strategy.on_market_event(event)
                
            self.portfolio_manager.on_market_event(event)
            self.execution_handler.on_market_event(event)

        elif event.type == EventType.SIGNAL:
            self.portfolio_manager.on_signal_event(event)

        elif event.type == EventType.ORDER:
            self.execution_handler.on_order_event(event)

        elif event.type == EventType.FILL:
            self.portfolio_manager.on_fill_event(event)

        elif event.type == EventType.DAILY_UPDATE:
            self.portfolio_manager.on_daily_update_event(event)

        else:
            logging.warning(f"Unknown event type received: {event.type}")