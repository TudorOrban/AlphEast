from typing import Any, Dict, List, Optional

from alpheast.shared.plotting import PerformancePlotter


class BacktestResults:
    """
    Class containing the results of the Backtest
    """
    def __init__(
        self,
        performance_metrics: Dict[str, Any],
        daily_values: List[Dict[str, Any]],
        benchmark_daily_values: List[Dict[str, Any]],
        trade_log: List[Dict[str, Any]],
        final_portfolio_summary: Dict[str, Any],
        start_date: Any,
        end_date: Any,
        initial_cash: float
    ):
        self.performance_metrics = performance_metrics
        self.daily_values = daily_values
        self.benchmark_daily_values = benchmark_daily_values
        self.trade_log = trade_log
        self.final_portfolio_summary = final_portfolio_summary
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
    
    def print_summary(self):
        """Prints a concise summary of the backtest results."""
        print("\n--- Backtest Results Summary ---")
        print(f"Initial Cash: ${self.initial_cash:.2f}")
        print(f"Final Cash: ${self.final_portfolio_summary["cash"]:.2f}")
        print(f"Final Holdings: {self.final_portfolio_summary["holdings"]}")
        print(f"Total Trades: {len(self.trade_log)}")

        if "strategy" in self.performance_metrics and "error" not in self.performance_metrics["strategy"]:
            print("\n--- Performance Metrics (Strategy) ---")
            for metric, value in self.performance_metrics["strategy"].items():
                print(f"{metric.replace('_', ' ').title()}: {value}")
        elif "strategy" in self.performance_metrics and "error" in self.performance_metrics["strategy"]:
            print(f"\n--- Strategy Performance Error ---")
            print(self.performance_metrics['strategy']['error'])

        if "benchmark" in self.performance_metrics and "error" not in self.performance_metrics["benchmark"]:
            print("\n--- Performance Metrics (Benchmark) ---")
            for metric, value in self.performance_metrics["benchmark"].items():
                print(f"{metric.replace('_', ' ').title()}: {value}")
        elif "benchmark" in self.performance_metrics and "error" in self.performance_metrics["benchmark"]:
            print(f"\n--- Benchmark Performance Error ---")
            print(self.performance_metrics['benchmark']['error'])
        print("-----------------------------------")

    def plot_equity_curve(self, title: Optional[str] = None):
        """Plots the portfolio equity curve and benchmark."""
        plotter = PerformancePlotter()
        default_title = f"Portfolio Equity Curve: {self.start_date} to {self.end_date}"
        plotter.plot_equity_curve(
            daily_values=self.daily_values,
            benchmark_daily_values=self.benchmark_daily_values,
            title=title if title else default_title
        )