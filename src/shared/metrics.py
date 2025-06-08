
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252

def calculate_performance_metrics(
    daily_values: List[Dict[str, Any]],
    trade_log: List[Dict[str, Any]],
    risk_free_trade: float = 0.0,
    benchmark_daily_values: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Calculates a set of common backtesting performance metrics.

    Args:
        daily_values: List of dictionaries from Portfolio.daily_values.
                      Each dict should have 'date' and 'total_value'.
        trade_log: List of dictionaries from Portfolio.trade_log.
        risk_free_rate: Annual risk-free rate for Sharpe Ratio calculation.

    Returns:
        A dictionary containing various performance metrics.
    """
    if not daily_values:
        return {"error": "No daily values to calculate metrics."}
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(daily_values)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    df["total_value"] = pd.to_numeric(df["total_value"])

    # Compte daily returns
    df["daily_return"] = df["total_value"].pct_change()
    df = df.dropna()
    if df.empty:
        return {"error": "Not enough data to calculate daily returns or metrics."}
    
    # --- Core Metrics ---
    initial_value = df["total_value"].iloc[0]
    final_value = df["total_value"].iloc[-1]

    # Total Return
    total_return = (final_value / initial_value) - 1.0

    # Annualized Return
    num_trading_days = len(df)
    if num_trading_days > 0:
        annualization_factor_return = TRADING_DAYS_PER_YEAR / num_trading_days
        annualized_return = (1 + total_return) ** annualization_factor_return - 1
    else:
        annualized_return = 0.0

    # Annualized Volatility
    daily_volatility = df["daily_return"].std()
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Sharpe Ratio
    if annualized_volatility != 0:
        sharpe_ratio = (annualized_return - risk_free_trade) / annualized_volatility
    else:
        sharpe_ratio = np.nan

    # Max Drawdown
    df["peak"] = df["total_value"].cummax()
    df["drawdown"] = (df["total_value"] - df["peak"]) / df["peak"]
    max_drawdown = df["drawdown"].min()

    metrics = {
        "initial_portfolio_value": round(float(initial_value)),
        "final_portfolio_value": round(float(final_value)),
        "total_return": round(total_return * 100, 2),
        "annualized_return": round(annualized_return * 100, 2),
        "annualized_volatility": round(annualized_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2) if not pd.isna(sharpe_ratio) else "N/A",
        "max_drawdown": round(max_drawdown * 100, 2),
        "total_trades": len(trade_log),
    }

    return metrics