
from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List


class BenchmarkCalculator:
    """
    Manages the calculation and tracking of benchmark portfolio values.
    """
    def __init__(
        self, 
        symbols: List[str],
        transaction_cost_percent: Decimal = Decimal("0.001"),
        slippage_percent: Decimal = Decimal("0.0005")
    ):
        self.symbols = symbols
        self._benchmark_holdings: Dict[str, Decimal] = {}
        self._benchmark_daily_values: List[Dict[str, Any]] = []
        self._benchmark_initialized: bool = False
        self.transaction_cost_percent = transaction_cost_percent
        self.slippage_percent = slippage_percent

        logging.info(f"BenchmarkCalculator initialized for symbols: {', '.join(self.symbols)}")

    def initialize_benchmark_holdings(self, initial_cash_total: Decimal, current_market_prices: Dict[str, Decimal]):
        """
        Initializes the benchmark holdings by equally weighting the initial cash
        across all symbols. This is called once at the first daily update.
        """
        if self._benchmark_initialized:
            logging.debug("Benchmark already initialized. Skipping re-initialization.")
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
            price_at_initialization = current_market_prices[symbol]

            price_with_slippage = price_at_initialization * (Decimal("1") + self.slippage_percent)
            if price_with_slippage <= Decimal("0"):
                logging.warning(f"Calculated effective buy price for {symbol} is zero or negative ({price_with_slippage:.2f}). Skipping allocation for this symbol.")
                continue
            
            effective_cost_per_share_with_fees = price_with_slippage * (Decimal("1") + self.transaction_cost_percent)
            if effective_cost_per_share_with_fees <= Decimal("0"):
                 logging.warning(f"Effective cost per share for {symbol} (incl. fees) is zero or negative ({effective_cost_per_share_with_fees:.2f}). Skipping allocation for this symbol.")
                 continue

            quantity = (cash_per_symbol / effective_cost_per_share_with_fees).quantize(Decimal("1")) # Quantize to whole shares

            if quantity <= Decimal("0"):
                logging.warning(f"Calculated zero or negative quantity for {symbol} with cash {cash_per_symbol:.2f}. Skipping allocation for this symbol.")
                continue

            self._benchmark_holdings[symbol] = quantity
            logging.info(
                f"Benchmark initialized for {symbol}: Bought {quantity} shares "
                f"at effective price ${price_with_slippage:.2f} (incl. slippage and fees), "
                f"investing ${cash_per_symbol:.2f}."
            )
       
        if self._benchmark_holdings:
            self._benchmark_initialized = True
        else:
            logging.warning("Benchmark could not be initialized for any symbol after accounting for frictions. Total benchmark value will be 0.")
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
