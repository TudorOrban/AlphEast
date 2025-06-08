
from datetime import datetime
from decimal import Decimal, getcontext
import logging
from typing import Any, Dict, List, Optional


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
    
    def buy(self, symbol: str, quantity: Decimal, price: Decimal, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Executes a buy order.

        Args:
            symbol: The stock symbol to buy.
            quantity: Number of shares to buy.
            price: Execution price per share.
            timestamp: The datetime of the trade.

        Returns:
            A dictionary representing the trade, or None if the trade cannot be executed.
        """
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        trade_cost = quantity * price
        fees = self._calculate_cost(quantity, price)
        total_cost = trade_cost + fees

        if not self.can_buy(price, quantity):
            logging.warning(f"Insufficient cash to buy {quantity} of {symbol} at ${price:.2f}.")
            return None

        self.cash -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, Decimal("0")) + quantity

        trade_record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "type": "BUY",
            "quantity": float(quantity),
            "price": float(price),
            "fees": float(fees),
            "total_cost": float(total_cost),
            "cash_after": float(self.cash),
            "holdings_after": {s: float(q) for s, q in self.holdings.items()} # Convert holdings to float for logging
        }
        self.trade_log.append(trade_record)
        logging.debug(f"BUY {float(quantity):.2f} {symbol} @ ${float(price):.2f}. Cash: ${self.cash:.2f}")
        return trade_record

    def sell(self, symbol: str, quantity: Decimal, price: Decimal, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Executes a sell order.

        Args:
            symbol: The stock symbol to sell.
            quantity: Number of shares to sell.
            price: Execution price per share.
            timestamp: The datetime of the trade.

        Returns:
            A dictionary representing the trade, or None if the trade cannot be executed.
        """
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        current_holding = self.get_holding_quantity(symbol)
        if current_holding < quantity:
            logging.warning(f"Attempted to sell {quantity} of {symbol} but only {current_holding} held.")
            quantity = current_holding
            if quantity == Decimal('0'):
                return None

        trade_revenue = quantity * price
        fees = self._calculate_cost(quantity, price)
        net_revenue = trade_revenue - fees

        self.cash += net_revenue
        self.holdings[symbol] -= quantity
        
        if self.holdings[symbol] <= Decimal('0'):
            del self.holdings[symbol]

        trade_record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "type": "SELL",
            "quantity": float(quantity),
            "price": float(price),
            "fees": float(fees),
            "net_revenue": float(net_revenue),
            "cash_after": float(self.cash),
            "holdings_after": {s: float(q) for s, q in self.holdings.items()}
        }
        self.trade_log.append(trade_record)
        logging.debug(f"SELL {float(quantity):.2f} {symbol} @ ${float(price):.2f}. Cash: ${self.cash:.2f}")
        return trade_record

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
            "final_cash": float(self.cash),
            "final_holdings": {s: float(q) for s, q in self.holdings.items()},
            "total_trades": len(self.trade_log)
        }

    def _calculate_cost(self, quantity: Decimal, price: Decimal) -> Decimal:
        trade_value = quantity * price
        return trade_value * self.transaction_cost_percent
    