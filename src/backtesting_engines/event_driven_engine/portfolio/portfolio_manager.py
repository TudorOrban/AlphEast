from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from src.backtesting_engines.event_driven_engine.position_sizing.examples.fixed_allocation_sizing import FixedAllocationSizing
from src.backtesting_engines.event_driven_engine.position_sizing.base_position_sizing import BasePositionSizing
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.models.event import FillEvent, MarketEvent, OrderEvent, SignalEvent
from src.shared.portfolio import Portfolio
from src.shared.signal import Signal


class PortfolioManager:
    """
    Manages the portfolio's cash and holdings, processes signals from strategies,
    and generates orders for the execution handler.
    It also processes fills to update the actual portfolio state.
    """
    def __init__(
        self,
        event_queue: EventQueue,
        initial_cash: float = 100000.0,
        transaction_cost_percent: Decimal = Decimal("0.001"),
        position_sizing_method: BasePositionSizing = None
    ):
        self.event_queue = event_queue
        self.portfolio_account = Portfolio(initial_cash, transaction_cost_percent)
        self._latest_market_prices: Dict[str, Decimal] = {}
        self._current_date: Optional[datetime.date] = None
        self.position_sizing_method = position_sizing_method or FixedAllocationSizing(0.05)
        logging.info(f"PortfolioManager initialized. Initial cash: ${self.portfolio_account.cash:.2f}")

    def on_market_event(self, event: MarketEvent):
        """
        Processes a MarketEvent. Updates the latest market prices cache and
        records the portfolio's daily value if a new day has started.
        """
        self._latest_market_prices[event.symbol] = Decimal(str(event.data["close"]))

        if self._current_date is None or event.timestamp.date() > self._current_date:
            self._current_date = event.timestamp.date()
            self.portfolio_account.record_daily_value(self._current_date, self._latest_market_prices)
            logging.debug(f"Portfolio value recorded for {self._current_date}. Current value: ${self.portfolio_account.get_total_value(self._latest_market_prices):.2f}")

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

        if event.direction == Signal.BUY.value:
            if current_holding == Decimal("0"):
                calculated_quantity = self.position_sizing_method.calculate_quantity(
                    symbol=event.symbol,
                    direction=event.direction,
                    current_price=current_price,
                    portfolio_cash=self.portfolio_account.cash,
                    portfolio_holdings=self.portfolio_account.holdings,
                )

                if calculated_quantity <= Decimal("0"):
                    logging.warning(f"Calculated quantity for {event.symbol} is {calculated_quantity}. Skipping BUY signal on {event.timestamp.date()}.")
                    return

                if self.portfolio_account.can_buy(current_price, calculated_quantity):
                    order_event = OrderEvent(
                        symbol=event.symbol,
                        timestamp=event.timestamp,
                        direction="BUY",
                        quantity=calculated_quantity,
                        order_type="MARKET",
                        price=current_price
                    )
                    self.event_queue.put(order_event)
                    logging.info(f"PortfolioManager placed BUY order for {calculated_quantity} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}")
                else:
                    logging.warning(f"Not enough cash to BUY {calculated_quantity} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}. Current cash: ${self.portfolio_account.cash:.2f}")
            else:
                logging.debug(f"Already holding {event.symbol}. Skipping BUY signal on {event.timestamp.date()}.")

        elif event.direction == Signal.SELL.value:
            if current_holding > Decimal("0"):
                quantity_to_sell = current_holding
                order_event = OrderEvent(
                    symbol=event.symbol,
                    timestamp=event.timestamp,
                    direction="SELL",
                    quantity=quantity_to_sell,
                    order_type="MARKET",
                    price=current_price
                )
                self.event_queue.put(order_event)
                logging.info(f"PortfolioManager placed SELL order for {quantity_to_sell} of {event.symbol} at {current_price:.2f} on {event.timestamp.date()}")
            else:
                logging.debug(f"Not holding {event.symbol}. Skipping SELL signal on {event.timestamp.date()}.")


    def on_fill_event(self, event: FillEvent):
        """
        Processes a FillEvent from the execution handler. Updates the actual
        cash and holdings of the portfolio.
        """
        if event.successful:
            if event.direction == "BUY":
                self.portfolio_account.buy(
                    symbol=event.symbol,
                    quantity=event.quantity,
                    price=event.fill_price,
                    timestamp=event.timestamp,
                    commission=event.commission
                )
            elif event.direction == "SELL":
                self.portfolio_account.sell(
                    symbol=event.symbol,
                    quantity=event.quantity,
                    price=event.fill_price,
                    timestamp=event.timestamp,
                    commission=event.commission
                )
            logging.info(f"Portfolio updated: {event.direction} {event.quantity} of {event.symbol} at {event.fill_price:.2f}. New cash: ${self.portfolio_account.cash:.2f}")
        else:
            logging.warning(f"Fill for {event.symbol} on {event.timestamp.date()} was not successful.")

    # --- Methods to retrieve final performance data for analysis ---
    def get_daily_values(self) -> List[Dict[str, Any]]:
        return self.portfolio_account.daily_values

    def get_trade_log(self) -> List[Dict[str, Any]]:
        return self.portfolio_account.trade_log

    def get_summary(self) -> Dict[str, Any]:
        return self.portfolio_account.get_summary()
