

import logging
from typing import Any, Dict, List

from matplotlib import pyplot as plt
import pandas as pd


class PerformancePlotter:
    """
    A class for visualizing backtesting performance metrics
    """
    def __init__(self):
        if plt is None:
            logging.error("Matplotlib is not available")
            self.plotting_enabled = False
        else:
            plt.style.use('seaborn-v0_8-darkgrid') 
            self.plotting_enabled = True

    def plot_equity_curve(
        self, 
        daily_values: List[Dict[str, Any]], 
        benchmark_daily_values: List[Dict[str, Any]], 
        title: str = "Portfolio Equity Curve"
    ):
        if not self.plotting_enabled:
            return
        if not daily_values:
            logging.warning(f"Cannot plot equity curve: No daily values provided for '{title}'.")
            return
        
        df_strategy = pd.DataFrame(daily_values)
        df_strategy["date"] = pd.to_datetime(df_strategy["date"])
        df_strategy = df_strategy.set_index("date")
        df_strategy["value"] = pd.to_numeric(df_strategy["value"])
        df_strategy = df_strategy.sort_index()
        
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(df_strategy.index, df_strategy["value"], label="Strategy Value", color="royalblue", linewidth=2)

        initial_value_strategy = df_strategy["value"].iloc[0]
        ax.axhline(y=initial_value_strategy, color="grey", linestyle="--", linewidth=1, label="Initial Capital")

        # Plot Benchmark Equity Curve if provided
        if benchmark_daily_values:
            if not benchmark_daily_values:
                logging.warning(f"Benchmark daily values list is empty, skipping benchmark plot for '{title}'.")
            else:
                df_benchmark = pd.DataFrame(benchmark_daily_values)
                df_benchmark["date"] = pd.to_datetime(df_benchmark["date"])
                df_benchmark = df_benchmark.set_index("date")
                df_benchmark["value"] = pd.to_numeric(df_benchmark["value"])
                df_benchmark = df_benchmark.sort_index() # Ensure chronological order

                ax.plot(df_benchmark.index, df_benchmark["value"], label="Benchmark Value", color="darkorange", linestyle="--", linewidth=1.5)

        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Portfolio Value ($)", fontsize=12)
        ax.tick_params(axis="both", which="major", labelsize=10)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.7)

        fig.autofmt_xdate()

        plt.tight_layout()
        plt.show()