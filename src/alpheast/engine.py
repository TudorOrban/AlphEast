from decimal import Decimal
import logging
from typing import Dict, List, Optional

from alpheast.data.price_bar_client import PriceBarClient
from alpheast.models.backtest_results import BacktestResults
from alpheast.events.event_queue import EventQueue
from alpheast.handlers.database_data_handler import DatabaseDataHandler
from alpheast.handlers.simulated_execution_handler import SimulatedExecutionHandler
from alpheast.models.price_bar import PriceBar
from alpheast.models.backtest_config import BacktestConfig
from alpheast.events.event_enums import EventType
from alpheast.portfolio.portfolio_manager import PortfolioManager
from alpheast.strategy.base_strategy import BaseStrategy
from alpheast.position_sizing.base_position_sizing import BasePositionSizing
from alpheast.shared.metrics import calculate_performance_metrics
from alpheast.shared.plotting import PerformancePlotter

class BacktestingEngine:
    """
    Orchestrates the event-driven backtesting process.
    Initializes all components and runs the main event loop.
    """
    def __init__(
        self,
        config: BacktestConfig,
        price_data: Dict[str, List[PriceBar]], # Symbol -> its price data
        data_client: Optional[PriceBarClient],
        strategies: List[BaseStrategy],
        position_sizing_method: Optional[BasePositionSizing] = None
    ):
        self.config = config
        self.event_queue = EventQueue()

        decimal_transaction_cost = Decimal(str(self.config.transaction_cost_percent))
        decimal_slippage_percent = Decimal(str(self.config.slippage_percent))

        self.data_handler = DatabaseDataHandler(
            event_queue=self.event_queue,
            symbols=self.config.symbols,
            price_data=price_data,
            data_client=data_client,
            start_date=self.config.start_date,
            end_date=self.config.end_date,    
            interval=self.config.interval   
        )

        self.strategies: List[BaseStrategy] = []
        for strategy_instance in strategies:
            strategy_instance.set_event_queue(self.event_queue)
            self.strategies.append(strategy_instance)
        
        self.portfolio_manager = PortfolioManager(
            event_queue=self.event_queue,
            initial_cash=self.config.initial_cash,
            transaction_cost_percent=decimal_transaction_cost,
            position_sizing_method=position_sizing_method,
            symbols=self.config.symbols
        )

        self.execution_handler = SimulatedExecutionHandler(
            event_queue=self.event_queue,
            transaction_cost_percent=decimal_transaction_cost,
            slippage_percent=decimal_slippage_percent
        )

        self.plotter = PerformancePlotter()

        logging.info("New Backtester initialized with config")
        
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