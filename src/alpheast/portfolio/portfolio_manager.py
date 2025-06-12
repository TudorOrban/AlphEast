from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid
from alpheast.portfolio.benchmark_calculator import BenchmarkCalculator
from alpheast.position_sizing.base_position_sizing import BasePositionSizing
from alpheast.events.event_queue import EventQueue
from alpheast.events.event_enums import OrderType
from alpheast.events.event import DailyUpdateEvent, FillEvent, MarketEvent, OrderEvent, SignalEvent
from alpheast.models.signal import Signal
from alpheast.portfolio.portfolio import Portfolio
from alpheast.position_sizing.common.fixed_allocation_sizing import FixedAllocationSizing


class PortfolioManager:
    """
    Manages the portfolio's cash and holdings, processes signals from strategies,
    and generates orders for the execution handler.
    It also processes fills to update the actual portfolio state.
    """
    def __init__(
        self,
        event_queue: EventQueue,
        symbols: List[str] = [],
        initial_cash: float = 100_000.0,
        transaction_cost_percent: Decimal = Decimal("0.001"),
        slippage_percent: Decimal = Decimal("0.0005"),
        position_sizing_method: Optional[BasePositionSizing] = None,
    ):
        self.event_queue = event_queue
        self.portfolio_account = Portfolio(initial_cash, transaction_cost_percent)
        self._latest_market_prices: Dict[str, Decimal] = {}
        self._current_date: Optional[datetime.date] = None
        
        self._daily_values: List[Dict[str, Any]] = []
        self._trade_log: List[Dict[str, Any]] = []
        
        self.position_sizing_method = position_sizing_method or FixedAllocationSizing(0.05)
        
        self.symbols = symbols
        self.benchmark_calculator = BenchmarkCalculator(symbols, transaction_cost_percent, slippage_percent)
        self._pending_orders: Dict[str, OrderEvent] = {}

        self.slippage_percent = slippage_percent

        logging.info(f"PortfolioManager initialized. Initial cash: ${self.portfolio_account.cash:.2f}")

    def on_market_event(self, event: MarketEvent):
        """
        Processes a MarketEvent. Updates the latest market prices cache and
        records the portfolio's daily value if a new day has started.
        """
        self._latest_market_prices[event.symbol] = Decimal(str(event.data["close"]))
        
    def on_signal_event(self, event: SignalEvent):
        """
        Processes a SignalEvent from the strategy. 
        Decides whether to place an order by generating an OrderEvent.
        """
        if event.symbol not in self._latest_market_prices:
            logging.warning(f"Cannot process SignalEvent for {event.symbol} on {event.timestamp.date()}: No market data available yet.")
            return
        
        current_price = self._latest_market_prices[event.symbol]
        current_holding = self.portfolio_account.get_holding_quantity(event.symbol)

        cash_for_new_order_consideration = self.portfolio_account.cash
        for order_id, order in self._pending_orders.items():
            if order.direction == Signal.BUY:
                estimated_pending_fill_price = order.price * (Decimal("1") + self.slippage_percent)
                estimated_pending_fill_price = max(Decimal("0.01"), estimated_pending_fill_price)

                estimated_pending_cost = (order.quantity * estimated_pending_fill_price) * (Decimal("1") + self.portfolio_account.transaction_cost_percent)
                cash_for_new_order_consideration -= estimated_pending_cost
                
        cash_for_new_order_consideration = max(Decimal("0"), cash_for_new_order_consideration)


        if event.direction == Signal.BUY:
            self._buy_on_signal_event(event, current_holding, current_price, cash_for_new_order_consideration)
        elif event.direction == Signal.SELL:
            self._sell_on_signal_event(event, current_holding, current_price)

    def _buy_on_signal_event(
        self, 
        event: SignalEvent,
        current_holding: Decimal,
        current_price: Decimal,
        cash_available_for_new_order: Decimal
    ):
        if current_holding == Decimal("0"):
            calculated_quantity = self.position_sizing_method.calculate_quantity(
                symbol=event.symbol,
                direction=event.direction,
                current_price=current_price,
                portfolio_cash=cash_available_for_new_order,
                portfolio_holdings=self.portfolio_account.holdings,
                portfolio_current_value=self.portfolio_account.get_total_value(self._latest_market_prices), # Pass current total value
                latest_market_prices=self._latest_market_prices 
            )

            if calculated_quantity <= Decimal("0"):
                logging.warning(f"Calculated quantity for {event.symbol} is {calculated_quantity}. Skipping BUY signal on {event.timestamp.date()}.")
                return

            estimated_fill_price_with_slippage = current_price * (Decimal("1") + self.slippage_percent)
            estimated_fill_price_with_slippage = max(Decimal("0.01"), estimated_fill_price_with_slippage) 
            estimated_total_cost = (calculated_quantity * estimated_fill_price_with_slippage) * \
                                   (Decimal("1") + self.portfolio_account.transaction_cost_percent)
            
            if cash_available_for_new_order >= estimated_total_cost:
                order_event = OrderEvent(
                    order_id=str(uuid.uuid4()),
                    symbol=event.symbol,
                    timestamp=event.timestamp,
                    direction=Signal.BUY,
                    quantity=calculated_quantity,
                    order_type=OrderType.MARKET,
                    price=current_price
                )
                self.event_queue.put(order_event)
                self._pending_orders[order_event.order_id] = order_event
                logging.info(f"PortfolioManager placed BUY order for {calculated_quantity} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}")
            else:
                logging.warning(f"Not enough cash to BUY {calculated_quantity} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}. Current cash: ${self.portfolio_account.cash:.2f}")
        else:
            logging.debug(f"Already holding {event.symbol}. Skipping BUY signal on {event.timestamp.date()}.")

    def _sell_on_signal_event(
        self,
        event: SignalEvent,
        current_holding: Decimal,
        current_price: Decimal
    ):
        if current_holding <= Decimal("0"):
            logging.debug(f"Not holding {event.symbol}. Skipping SELL signal on {event.timestamp.date()}.")
            return
        
        # Sell all current holding
        quantity_to_sell = current_holding

        order_event = OrderEvent(
            order_id=str(uuid.uuid4()),
            symbol=event.symbol,
            timestamp=event.timestamp,
            direction=Signal.SELL,
            quantity=quantity_to_sell,
            order_type=OrderType.MARKET,
            price=current_price
        )
        self.event_queue.put(order_event)
        self._pending_orders[order_event.order_id] = order_event
        logging.info(f"PortfolioManager placed SELL order for {quantity_to_sell} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}")

    def on_fill_event(self, event: FillEvent):
        """
        Processes a FillEvent from the execution handler. Updates the actual
        cash and holdings of the portfolio.
        """
        if event.order_id in self._pending_orders:
            del self._pending_orders[event.order_id]
        else:
            logging.warning(f"Received FillEvent for unknown or already processed order ID: {event.order_id}. This might indicate a logic error or out-of-order event processing.")

        if event.successful:
            if event.direction == Signal.BUY:
                self.portfolio_account.buy(
                    symbol=event.symbol,
                    quantity=event.quantity,
                    price=event.fill_price,
                    timestamp=event.timestamp,
                    commission=event.commission
                )
            elif event.direction == Signal.SELL:
                self.portfolio_account.sell(
                    symbol=event.symbol,
                    quantity=event.quantity,
                    price=event.fill_price,
                    timestamp=event.timestamp,
                    commission=event.commission
                )
            self._trade_log.append({
                "timestamp": event.timestamp,
                "symbol": event.symbol,
                "direction": event.direction,
                "quantity": event.quantity,
                "price": event.fill_price, 
                "commission": event.commission,
                "successful": event.successful,
                "order_id": event.order_id
            })
            logging.info(f"Portfolio updated: {event.direction} {event.quantity} of {event.symbol} at {event.fill_price:.2f}. New cash: ${self.portfolio_account.cash:.2f}")
        else:
            logging.warning(f"Fill for {event.symbol} on {event.timestamp.date()} was not successful.")

    def on_daily_update_event(self, event: DailyUpdateEvent):
        """
        Processes a DailyUpdateEvent, triggering daily portfolio value calculations
        for both the strategy and the benchmark by calling helper functions.
        """
        self._current_date = event.timestamp.date()
        if not self.benchmark_calculator.is_initialized():
            self.benchmark_calculator.initialize_benchmark_holdings(
                self.portfolio_account.initial_cash,
                self._latest_market_prices
            )
            if not self.benchmark_calculator.is_initialized():
                logging.warning(f"Benchmark could not be initialized on {self._current_date}. Daily benchmark values will be 0.")

        self._calculate_and_record_strategy_value()
        self.benchmark_calculator.calculate_and_record_benchmark_value( # NEW: Delegate benchmark calculation
            self._current_date, 
            self._latest_market_prices
        )

    # --- Methods to retrieve final performance data for analysis ---
    def get_daily_values(self) -> List[Dict[str, Any]]:
        return self._daily_values

    def get_benchmark_daily_values(self) -> List[Dict[str, Any]]:
        """Returns the benchmark's daily portfolio value history."""
        return self.benchmark_calculator.get_daily_values()

    def get_trade_log(self) -> List[Dict[str, Any]]:
        return self._trade_log

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a summary of the final portfolio state.
        This correctly calls the portfolio_account's summary.
        """
        return {
            "cash": self.portfolio_account.cash,
            "holdings": self.portfolio_account.holdings,
            "total_value": self.portfolio_account.get_total_value(self._latest_market_prices)
        }
    
    def _calculate_and_record_strategy_value(self):
        """
        Calculates the strategy's total portfolio value for the current day
        and appends it to the daily values history.
        """
        if self._latest_market_prices:
            current_portfolio_value = self.portfolio_account.get_total_value(self._latest_market_prices)
        else:
            current_portfolio_value = self.portfolio_account.cash
            logging.warning(f"No market prices available on {self._current_date} for strategy value calculation. Using cash balance.")

        self._daily_values.append({
            "date": self._current_date,
            "value": current_portfolio_value
        })
        logging.debug(f"Strategy portfolio value on {self._current_date}: ${current_portfolio_value:.2f}")