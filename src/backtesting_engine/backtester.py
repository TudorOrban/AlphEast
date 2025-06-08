
from datetime import datetime
from decimal import Decimal
import logging
from typing import List
from src.analysis.plotting import PerformancePlotter
from src.analysis.metrics import calculate_performance_metrics
from src.data.eod_prices.model import EODPrice
from src.data.eod_prices.repository import EODPriceRepository
from src.portfolio.model import Portfolio
from src.strategy.base_strategy import BaseStrategy
from src.strategy.models.signal import Signal


class Backtester:
    def __init__(self, strategy: BaseStrategy, initial_cash: float = 100000.0):
        """
        Initializes the backtesting engine.

        Args:
            strategy: An instance of a concrete strategy inheriting from BaseStrategy.
            initial_cash: Starting cash for the portfolio.
        """
        self.strategy = strategy
        self.portfolio = Portfolio(initial_cash=initial_cash)
        self.repository = EODPriceRepository()
        self.plotter = PerformancePlotter()

        self.strategy.set_environment(self.portfolio, self)

        logging.info("Backtester initialized")

    def run(self, symbol: str, start_date: datetime, end_date: datetime):
        """
        Runs the backtest simulation.

        Args:
            symbol: The financial instrument symbol to backtest.
            start_date: The start date for the backtest (datetime object).
            end_date: The end date for the backtest (datetime object).
        """
        logging.info(f"Starting backtest for {symbol} from {start_date.date()} to {end_date.date()}")

        symbol_prices: List[EODPrice] = self.repository.get_eod_prices_by_symbol(
            symbol=symbol, start_date=start_date.date(), end_date=end_date.date()
        )

        if not symbol_prices:
            logging.warning(f"No EOD prices found for {symbol} in the specified range. Aborting backtest.")
            return
        logging.info(f"Loaded {len(symbol_prices)} EOD prices for backtesting.")

        self.strategy.initialize()

        for i, current_bar in enumerate(symbol_prices):
            current_date_dt = current_bar.time

            required_lookback = max(
                getattr(self.strategy, "slow_period", 0),
                getattr(self.strategy, "fast_period", 0)
            )

            history_window: List[EODPrice] = []
            if i > 0 and required_lookback > 0:
                history_window = symbol_prices[max(0, i - required_lookback):i]

            signal = self.strategy.on_data(current_bar, history_window)

            if signal == Signal.BUY:
                if self.portfolio.get_holding_quantity(symbol) == Decimal("0"):
                    quantity_to_trade = Decimal("10")
                    self.portfolio.buy(
                        symbol=symbol,
                        quantity=quantity_to_trade,
                        price=current_bar.close,
                        timestamp=current_date_dt
                    )
                else:
                    logging.debug(f"Strategy signaled BUY for {symbol} on {current_date_dt.date()} but already holding.")

            elif signal == Signal.SELL:
                current_holding = self.portfolio.get_holding_quantity(symbol)
                if current_holding > Decimal("0"):
                    self.portfolio.sell(
                        symbol=symbol,
                        quantity=current_holding,
                        price=current_bar.close,
                        timestamp=current_date_dt
                    )
                else:
                    logging.debug(f"Strategy signaled SELL for {symbol} on {current_date_dt.date()} but no position held.")
            
            current_prices_for_portfolio = {symbol: current_bar.close}
            self.portfolio.record_daily_value(current_date_dt.date(), current_prices_for_portfolio)

        logging.info("Backtest completed.")
        
        performance_metrics = calculate_performance_metrics(
            daily_values=self.portfolio.daily_values,
            trade_log=self.portfolio.trade_log
        )
        
        print("\n--- Backtest Summary ---")
        print(f"Initial Cash: ${self.portfolio.initial_cash:.2f}")
        print(f"Final Cash: ${self.portfolio.cash:.2f}")
        print(f"Final Holdings: {self.portfolio.holdings}")
        print(f"Total Trades: {len(self.portfolio.trade_log)}")
        print("\n--- Performance Metrics ---")
        for metric, value in performance_metrics.items():
            print(f"{metric.replace('_', ' ').title()}: {value}")
        print("------------------------")

        strategy_name = self.strategy.__class__.__name__
        plot_title = f"Portflio Equity Curve: {symbol} with {strategy_name}"
        self.plotter.plot_equity_curve(self.portfolio.daily_values, title=plot_title)

        return {
            "performance_metrics": performance_metrics,
            "daily_values": self.portfolio.daily_values,
            "trade_log": self.portfolio.trade_log,
            "final_portfolio_summary": self.portfolio.get_summary()
        }