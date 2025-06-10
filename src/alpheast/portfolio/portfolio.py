
from datetime import datetime
from decimal import Decimal, getcontext
import logging
from typing import Any, Dict, List


getcontext().prec = 10

class Portfolio:
    def __init__(self, initial_cash: float, transaction_cost_percent: Decimal = Decimal("0.001")):
        """
        Initializes the portfolio.

        Args:
            initial_cash: The starting cash balance for the backtest.
            transaction_cost_percent: Percentage cost per trade (e.g., 0.001 for 0.1%).
                                      Using Decimal for precision.
        """
        if initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")
        self.cash: Decimal = Decimal(str(initial_cash))
        self.holdings: Dict[str, Decimal] = {} # Symbol -> Quantity
        self.initial_cash: Decimal = Decimal(str(initial_cash))
        self.transaction_cost_percent: Decimal = transaction_cost_percent

        self.daily_values: List[Dict[str, Any]] = []
        self.trade_log: List[Dict[str, Any]] = []

        logging.info(f"Portfolio initialized with cash: ${self.cash:.2f}")

    def get_holding_quantity(self, symbol: str) -> Decimal:
        return self.holdings.get(symbol, Decimal("0"))
    
    def can_buy(self, price: Decimal, quantity: Decimal) -> bool:
        trade_cost = price * quantity
        total_cost_with_fees = trade_cost + self._calculate_cost(quantity, price)
        return self.cash >= total_cost_with_fees
    
    def buy(self, symbol: str, quantity: Decimal, price: Decimal, timestamp: datetime, commission: Decimal = Decimal('0.0')) -> Dict[str, Any]:
        """
        Executes a buy order, updates cash, holdings, and logs the trade.
        Assumes the order is valid (e.g., sufficient cash checked externally by PortfolioManager).
        Accepts commission directly from the fill event.
        """
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))
        commission = Decimal(str(commission))

        trade_cost_raw = quantity * price
        total_cost = trade_cost_raw + commission
        
        if self.cash < total_cost:
            logging.error(f"Attempted to buy {quantity} of {symbol} at {price:.2f} on {timestamp.date()} but insufficient cash! Cash: {self.cash:.2f}, Cost: {total_cost:.2f}")
            raise ValueError("Insufficient cash to perform buy operation (should be caught by PM).")

        self.cash -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, Decimal("0")) + quantity

        trade_info = {
            "timestamp": timestamp,
            "symbol": symbol,
            "type": "BUY",
            "quantity": quantity,
            "price": price,      
            "commission": commission,
            "total_cost": total_cost,
            "cash_after_trade": self.cash
        }
        self.trade_log.append(trade_info)
        logging.info(f"BUY {quantity} {symbol} @ ${price:.2f} (Comm: ${commission:.2f}) on {timestamp.date()}. New Cash: ${self.cash:.2f}")
        return trade_info

    def sell(self, symbol: str, quantity: Decimal, price: Decimal, timestamp: datetime, commission: Decimal = Decimal('0.0')) -> Dict[str, Any]:
        """
        Executes a sell order, updates cash, holdings, and logs the trade.
        Assumes the order is valid (e.g., sufficient holdings checked externally by PortfolioManager).
        Accepts commission directly from the fill event.
        """
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))
        commission = Decimal(str(commission))

        if self.holdings.get(symbol, Decimal("0")) < quantity:
            logging.error(f"Attempted to sell {quantity} of {symbol} on {timestamp.date()} but insufficient holdings! Holding: {self.holdings.get(symbol, Decimal('0'))}")
            raise ValueError(f"Insufficient holdings of {symbol} to perform sell operation.")

        trade_revenue_raw = price * quantity
        total_revenue = trade_revenue_raw - commission

        self.cash += total_revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == Decimal("0"):
            del self.holdings[symbol]

        trade_info = {
            "timestamp": timestamp,
            "symbol": symbol,
            "type": "SELL",
            "quantity": quantity,
            "price": price,
            "commission": commission,
            "total_revenue": total_revenue,
            "cash_after_trade": self.cash
        }
        self.trade_log.append(trade_info)
        logging.info(f"SELL {quantity} {symbol} @ ${price:.2f} (Comm: ${commission:.2f}) on {timestamp.date()}. New Cash: ${self.cash:.2f}")
        return trade_info
    
    def get_current_value(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """
        Calculates the current total value of the portfolio(cash + value of holdings).

        Args:
            current_prices: A dictionary of {symbol: current_price} for held assets.
                            This will be passed from the Backtester using the current day's close price.
        """
        holdings_value = Decimal("0")
        for symbol, quantity in self.holdings.items():
            if symbol in current_prices:
                holdings_value += quantity * current_prices[symbol]
            else:
                logging.warning(f"Price for {symbol} not available to calculate portfolio valule. Assuming 0.")
    
        return self.cash + holdings_value
    
    def get_total_value(self, current_market_prices: Dict[str, Decimal]) -> Decimal:
        """
        Calculates the total current value of the portfolio (cash + value of holdings).

        Args:
            current_market_prices: A dictionary mapping symbol (str) to its latest price (Decimal).
                                   This dict should contain prices for all symbols currently held.

        Returns:
            The total value of the portfolio as a Decimal.
        """
        total_holdings_value = Decimal("0")
        for symbol, quantity in self.holdings.items():
            if symbol in current_market_prices:
                price = current_market_prices[symbol]
                total_holdings_value += quantity * price
            else:
                logging.warning(f"Market price not available for held symbol '{symbol}' when calculating total value. Assuming 0 for this holding on this calculation.")
        
        return self.cash + total_holdings_value

    def record_daily_value(self, date: datetime.date, current_prices: Dict[str, Decimal]):
        """
        Records the portfolio's state and value at the end of a trading day.
        """
        total_value = self.get_current_value(current_prices)
        self.daily_values.append({
            "date": date,
            "total_value": float(total_value),
            "cash": float(self.cash),
            "holdings": {s: float(q) for s, q in self.holdings.items()}
        })

    def get_summary(self) -> Dict[str, Any]:
        """
        Provides a summary of the portfolio's final state.
        """
        return {
            "initial_cash": float(self.initial_cash),
            "cash": float(self.cash),
            "holdings": {s: float(q) for s, q in self.holdings.items()},
            "total_trades": len(self.trade_log)
        }

    def _calculate_cost(self, quantity: Decimal, price: Decimal) -> Decimal:
        trade_value = quantity * price
        return trade_value * self.transaction_cost_percent
    