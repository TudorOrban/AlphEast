
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252

def calculate_performance_metrics(
    daily_values: List[Dict[str, Any]],
    trade_log: List[Dict[str, Any]],
    risk_free_rate: float = 0.0,
    benchmark_daily_values: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Calculates a set of common backtesting performance metrics for the strategy
    and optionally for a benchmark.

    Args:
        daily_values: List of dictionaries from PortfolioManager.get_daily_values().
                      Each dict should have "date" and "value".
        trade_log: List of dictionaries from PortfolioManager.get_trade_log().
        risk_free_rate: Annual risk-free rate for Sharpe Ratio calculation.
        benchmark_daily_values: Optional list of dictionaries for benchmark equity.
                                Each dict should have "date" and "value".

    Returns:
        A dictionary containing various performance metrics, potentially nested for strategy and benchmark.
    """
    results = {}

    # --- Process Strategy Performance ---
    if not daily_values:
        logging.error("No daily values provided for strategy performance calculation.")
        results["strategy"] = {"error": "No daily values to calculate metrics."}
    else:
        df_strategy = pd.DataFrame(daily_values)
        df_strategy["date"] = pd.to_datetime(df_strategy["date"])
        df_strategy = df_strategy.set_index("date")
        df_strategy = df_strategy.sort_index() # Ensure chronological order

        if df_strategy.empty:
            logging.warning("Strategy DataFrame is empty after processing. Cannot calculate metrics.")
            results["strategy"] = {"error": "Not enough data to calculate daily returns or metrics for strategy."}
        else:
            strategy_metrics = _calculate_single_equity_metrics(df_strategy, trade_log, risk_free_rate)
            strategy_metrics["total_trades"] = len(trade_log) 
            results["strategy"] = strategy_metrics

    # --- Process Benchmark Performance (if provided) ---
    if benchmark_daily_values:
        if not benchmark_daily_values:
            logging.warning("Benchmark daily values list is empty, skipping benchmark metrics.")
        else:
            df_benchmark = pd.DataFrame(benchmark_daily_values)
            df_benchmark["date"] = pd.to_datetime(df_benchmark["date"])
            df_benchmark = df_benchmark.set_index("date")
            df_benchmark = df_benchmark.sort_index()

            if df_benchmark.empty:
                logging.warning("Benchmark DataFrame is empty after processing. Cannot calculate metrics.")
            else:
                benchmark_metrics = _calculate_single_equity_metrics(df_benchmark, [], risk_free_rate)
                benchmark_metrics["total_trades"] = "N/A"
                results["benchmark"] = benchmark_metrics

    return results


def _calculate_single_equity_metrics(
    df: pd.DataFrame,
    trade_log: List[Dict[str, Any]],
    risk_free_rate: float
) -> Dict[str, Any]:
    """
    Helper function to calculate metrics for a single equity curve (strategy or benchmark).
    """
    if df.empty:
        return {
            "initial_portfolio_value": 0.0,
            "final_portfolio_value": 0.0,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": "N/A",
            "max_drawdown": 0.0,
            "total_trades": len(trade_log)
        }

    df["value"] = df["value"].apply(lambda x: float(x) if isinstance(x, Decimal) else float(x))

    df["daily_return"] = df["value"].pct_change()
    df = df.dropna().copy()

    if df.empty:
        return {
            "initial_portfolio_value": 0.0,
            "final_portfolio_value": 0.0,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": "N/A",
            "max_drawdown": 0.0,
            "total_trades": len(trade_log) 
        }
    
    initial_value = df["value"].iloc[0]
    final_value = df["value"].iloc[-1]

    # Total Return
    total_return = (final_value / initial_value) - 1.0 if initial_value != 0 else 0.0

    # Annualized Return
    num_trading_days = len(df)
    if num_trading_days > 0 and (1 + total_return) >= 0: # Ensure base for power is non-negative
        annualization_factor_return = TRADING_DAYS_PER_YEAR / num_trading_days
        annualized_return = (1 + total_return) ** annualization_factor_return - 1
    else:
        annualized_return = 0.0 

    # Annualized Volatility
    daily_volatility = df["daily_return"].std()
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR) if not pd.isna(daily_volatility) else 0.0

    # Sharpe Ratio
    if annualized_volatility != 0:
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
    else:
        sharpe_ratio = np.nan

    # Max Drawdown
    df["peak"] = df["value"].cummax()
    df["drawdown"] = (df["value"] - df["peak"]) / df["peak"]
    max_drawdown = df["drawdown"].min() if not df["drawdown"].empty else 0.0

    metrics = {
        "initial_portfolio_value": round(float(initial_value), 2),
        "final_portfolio_value": round(float(final_value), 2),
        "total_return": round(total_return * 100, 2),
        "annualized_return": round(annualized_return * 100, 2),
        "annualized_volatility": round(annualized_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2) if not pd.isna(sharpe_ratio) else "N/A",
        "max_drawdown": round(max_drawdown * 100, 2),
    }
    return metrics

