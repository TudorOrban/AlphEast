# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-06-16 

### Added
- **Stepping Mode:** Introduced a new "stepping mode" for the backtesting engine, allowing users to advance through data point by data point. This is in contrast to the traditional `run()` method which processes all data at once.
- **`reset()` method:** Added a `reset()` method to the engine, enabling users to reset the engine's state, data, and orders for a fresh backtest.

### Changed
- **FIFO Order Fillage:** Modified the order fill logic to ensure a First-In, First-Out (FIFO) processing for all orders. This provides more predictable and realistic order execution.
- **Committed Order Queue:** Implemented a queue for committed orders to prevent potential race conditions during order processing and execution. This enhances the engine's stability and reliability.