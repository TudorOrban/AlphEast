# AlphEast Backtesting Engine

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![Documentation Status](https://readthedocs.org/projects/alpheast/badge/?version=latest)](https://alpheast.readthedocs.io/en/latest/?badge=latest)
---

## 🌟 Overview

AlphEast is an event-driven backtesting engine designed for developing and evaluating quantitative trading strategies. While still in its early stages of development, it provides a robust, extensible framework for simulating and evaluating multi-symbol trading strategies with realistic considerations like transaction costs and slippage.

Our goal is to offer a flexible tool for researchers and traders to quickly prototype and test their ideas, without getting bogged down in boilerplate.

---

## 📚 Documentation

For complete usage instructions, API reference, detailed examples, and guides, please visit our official documentation website:

https://alpheast.readthedocs.io/en/latest/

---

## ✨ Key Features

* **Event-Driven Architecture:** Simulates market conditions and trade executions with a clear, sequential event flow.
* **Multi-Symbol Backtesting:** Simultaneously test strategies across multiple financial instruments.
* **Pluggable Strategies:** Easily define and integrate your own custom trading strategies.
* **Customizable Position Sizing:** Implement various position sizing methods to manage risk and allocate capital.
* **Realistic Simulations:** Accounts for transaction costs (commissions) and slippage to provide more accurate results.
* **Performance Metrics & Visualization:** Generates standard trading performance metrics and plots equity curves for quick analysis.
* **Flexible Data Ingestion:** Designed to integrate with various data sources, from direct in-memory data to custom database repositories.

---

## 🚀 Quick Start

Get your first backtest running in minutes!

### Installation

```bash
pip install alpheast
```

### Basic Usage Example

```python
from datetime import datetime
from typing import Dict, List
from alpheast.config.data_source import DataSource, DataSourceType
from alpheast.engine import BacktestingEngine
from alpheast.config.backtest_config import BacktestingOptions
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar
from examples.basic.example_strategy import ExampleStrategy


if __name__ == "__main__":
    symbol = "AAPL"
    options = BacktestingOptions(
        symbols=[symbol],
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2025, 1, 1),
        interval=Interval.DAILY,
        initial_cash=100_000.0
    )

    price_bar_data: Dict[str, List[PriceBar]] = {
        symbol: [] # Provide your data
    }
    data_source = DataSource(
        type=DataSourceType.DIRECT,
        price_bar_data=price_bar_data,
    )

    engine = BacktestingEngine(
        options=options,
        data_source=data_source,
        strategies=[ExampleStrategy(symbol)],
    )
    
    results = engine.run()

    if results:
        results.print_summary()
        results.plot_equity_curve()
```

![equity-curve](https://raw.githubusercontent.com/TudorOrban/AlphEast/main/screenshots/equity_curve.png)

## ⚡️ Performance
AlphEast is designed for efficiency and demonstrates strong scaling characteristics with both the number of symbols and the backtesting duration. Below are some example execution times measured on a standard setup:

### **Execution Time (seconds)**

| Symbols \ Duration | 1 Year   | 5 Years  |
| :----------------- | :------- | :------- |
| **1** | 0.2124   | 0.9258   |
| **2** | 0.3027   | 1.2424   |
| **10** | 0.9525   | 3.6243   |

## Status
In mid stages of development.

## Contributing
All contributions are warmly welcomed. Head over to [CONTRIBUTING.md](https://github.com/TudorOrban/AlphEast/blob/main/CONTRIBUTING.md) for details.