

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

    def plot_equity_curve(self, daily_values: List[Dict[str, Any]], title: str = "Portfolio Equity Curve"):
        if not self.plotting_enabled:
            return
        if not daily_values:
            logging.warning(f"Cannot plot equity curve: No daily values provided for '{title}'.")
            return
        
        df = pd.DataFrame(daily_values)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df["total_value"] = pd.to_numeric(df["total_value"])

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(df.index, df["total_value"], label="Portfolio Value", color="royalblue")

        initial_value = df["total_value"].iloc[0]
        ax.axhline(y=initial_value, color="grey", linestyle="--", linewidth=1, label="Initial Capital")

        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Portfolio Value ($)", fontsize=12)
        ax.tick_params(axis="both", which="major", labelsize=10)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.7)

        fig.autofmt_xdate()

        plt.tight_layout()
        plt.show()