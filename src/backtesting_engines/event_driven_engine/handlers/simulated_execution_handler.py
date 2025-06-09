
from decimal import Decimal
import logging
from typing import Dict
from src.backtesting_engines.event_driven_engine.models.event_enums import OrderType
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.models.event import FillEvent, MarketEvent, OrderEvent
from src.backtesting_engines.event_driven_engine.handlers.execution_handler import ExecutionHandler


class SimulatedExecutionHandler(ExecutionHandler):
    """
    A concrete execution handler that simulates order execution.
    Currently, it assumes market orders are filled at the close price of the bar
    on which the order was generated. No slippage or partial fills are simulated.
    """
    def __init__(self, event_queue: EventQueue, transaction_cost_percent: Decimal = Decimal("0.001")):
        self.event_queue = event_queue
        # Cache latest known market prices to simulate fills
        self._latest_market_prices: Dict[str, Decimal] = {}
        self.transaction_cost_percent = transaction_cost_percent
    
    def on_market_event(self, event: MarketEvent):
        """
        Updates the internal cache of the latest market prices based on incoming MarketEvents.
        """
        if event.symbol in self._latest_market_prices and event.timestamp < self._latest_market_prices[event.symbol]["timestamp"]:
            return
        
        self._latest_market_prices[event.symbol] = {
            "price": Decimal(str(event.data["close"])),
            "timestamp": event.timestamp
        }
        logging.debug(f"ExecutionHandler updated latest price for {event.symbol} to {self._latest_market_prices[event.symbol]["price"]:.2f} on {event.timestamp.date()}")

    def on_order_event(self, event: OrderEvent):
        """
        Simulates the execution of an order.
        For simplicity, market orders are filled at the latest known close price.
        Limit orders are not yet supported.
        """
        if event.order_type == OrderType.LIMIT:
            logging.warning(f"Limit order for {event.symbol} on {event.timestamp.date()} not supported by SimulatedExecutionHandler. Order not filled.")
            failed_fill_event = FillEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                direction=event.direction,
                quantity=event.quantity,
                fill_price=Decimal('0.0'),
                commission=Decimal('0.0'),
                successful=False
            )
            self.event_queue.put(failed_fill_event)
            return
    
        self.process_market_order_event(event)

    def process_market_order_event(self, event: OrderEvent):
        try:
            fill_price_data = self._latest_market_prices.get(event.symbol)

            if not fill_price_data:
                logging.warning(f"No market data available for {event.symbol} to fill order on {event.timestamp.date()}. Skipping fill.")
                self.push_failed_fill_event(event)
                return

            fill_price = fill_price_data["price"]
            commission = (event.quantity * fill_price) * self.transaction_cost_percent
            
            fill_event = FillEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                direction=event.direction,
                quantity=event.quantity,
                fill_price=fill_price,
                commission=commission,
                successful=True
            )
            self.event_queue.put(fill_event)
            logging.info(f"Filled {event.direction} {event.quantity} of {event.symbol} at {fill_price:.2f} (Commission: {commission:.2f}) on {event.timestamp.date()}")

        except Exception as e:
            logging.error(f"Error simulating order fill for {event.symbol} on {event.timestamp.date()}: {e}", exc_info=True)
            self.push_failed_fill_event(event)

    def push_failed_fill_event(self, event: OrderEvent):
        failed_fill_event = FillEvent(
            symbol=event.symbol,
            timestamp=event.timestamp,
            direction=event.direction,
            quantity=event.quantity,
            fill_price=Decimal("0.0"),
            commission=Decimal("0.0"),
            successful=False
        )
        self.event_queue.put(failed_fill_event)