
from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List


class BenchmarkCalculator:
    """
    Manages the calculation and tracking of benchmark portfolio values.
    """
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self._benchmark_holdings: Dict[str, Decimal] = {}
        self._benchmark_daily_values: List[Dict[str, Any]] = []
        self._benchmark_initialized: bool = False
    

    def initialize_benchmark_holdings(self, initial_cash_total: Decimal, current_market_prices: Dict[str, Decimal]):
        """
        Initializes the benchmark holdings by equally weighting the initial cash
        across all symbols. This is called once at the first daily update.
        """
        if not self.symbols:
            logging.warning("No symbols provided to BenchmarkCalculator for initialization.")
            self._benchmark_initialized = True
            return
        
        available_symbols_for_benchmark = [s for s in self.symbols if s in current_market_prices and current_market_prices[s] > Decimal("0")]
        if not available_symbols_for_benchmark:
            logging.warning("No valid market prices available for any symbols to initialize benchmark. Skipping benchmark initialization.")
            self._benchmark_initialized = True
            return
        
        if len(available_symbols_for_benchmark) == 0:
            logging.warning("No valid symbols with positive prices to initialize benchmark. Skipping benchmark initialization.")
            self._benchmark_initialized = True
            return

        cash_per_symbol = initial_cash_total / Decimal(str(len(available_symbols_for_benchmark))) # Distribute only among available symbols

        for symbol in available_symbols_for_benchmark:
            if current_market_prices[symbol] > Decimal("0"):
                quantity = (cash_per_symbol / current_market_prices[symbol]).quantize(Decimal("1"))
                self._benchmark_holdings[symbol] = quantity
                logging.info(f"Benchmark initialized: Bought {quantity} of {symbol} at {current_market_prices[symbol]:.2f}")
            else:
                 logging.warning(f"Cannot initialize benchmark for {symbol}: current market price is zero or negative.")
       
        self._benchmark_initialized = True 

    def calculate_and_record_benchmark_value(self, current_date: datetime.date, latest_market_prices: Dict[str, Decimal]):
        """
        Calculates the benchmark's total portfolio value for the current day
        and appends it to the benchmark daily values history.
        """
        benchmark_value = Decimal("0")
        if self._benchmark_initialized:
            for symbol, quantity in self._benchmark_holdings.items():
                if symbol in latest_market_prices:
                    benchmark_value += quantity * latest_market_prices[symbol]
                else:
                    logging.warning(f"Benchmark symbol {symbol} has no market price on {current_date}. Its contribution to benchmark value will be 0 for today.")
        else:
            logging.debug(f"Benchmark not initialized. Benchmark value will be $0.00 on {current_date}.")
        
        self._benchmark_daily_values.append({
            "date": current_date,
            "value": benchmark_value
        })
        logging.debug(f"Benchmark portfolio value on {current_date}: ${benchmark_value:.2f}")

    def is_initialized(self) -> bool:
        return self._benchmark_initialized

    def get_daily_values(self) -> List[Dict[str, Any]]:
        return self._benchmark_daily_values
