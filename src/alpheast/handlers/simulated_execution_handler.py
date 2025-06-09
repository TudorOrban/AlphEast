
from decimal import Decimal
import logging
from typing import Any, Dict
from alpheast.models.signal import Signal
from alpheast.events.event_enums import OrderType
from alpheast.events.event_queue import EventQueue
from alpheast.events.event import FillEvent, MarketEvent, OrderEvent
from alpheast.handlers.execution_handler import ExecutionHandler


class SimulatedExecutionHandler(ExecutionHandler):
    """
    A concrete execution handler that simulates order execution.
    It simulates slippage for market orders and considers high/low for limit orders.
    """
    def __init__(
        self, 
        event_queue: EventQueue, 
        transaction_cost_percent: Decimal = Decimal("0.001"),
        slippage_percent: Decimal = Decimal("0.0005")
    ):
        self.event_queue = event_queue
        # Cache latest known market prices to simulate fills
        self._latest_market_prices: Dict[str, Dict[str, Any]] = {}
        self.transaction_cost_percent = transaction_cost_percent
        self.slippage_percent = slippage_percent

        self._open_orders: Dict[str, OrderEvent] = {}
        logging.info("SimulatedExecutionHandler initialized.")

    def on_market_event(self, event: MarketEvent):
        """
        Updates the internal cache of the latest market prices based on incoming MarketEvents.
        """
        self._latest_market_prices[event.symbol] = {
            "price": Decimal(str(event.data["close"])),
            "timestamp": event.timestamp,
            "open": Decimal(str(event.data["open"])),
            "high": Decimal(str(event.data["high"])),
            "low": Decimal(str(event.data["low"]))
        }
        logging.debug(f"ExecutionHandler updated latest price for {event.symbol} to {self._latest_market_prices[event.symbol]['price']:.2f} on {event.timestamp.date()}")

        orders_for_current_symbol_to_process = [
            order_id for order_id, order in self._open_orders.items() 
            if order.symbol == event.symbol
        ]
        for order_id in orders_for_current_symbol_to_process:
            if order_id not in self._open_orders:
                continue
            order = self._open_orders[order_id]
            if order.order_type == OrderType.MARKET:
                self._attempt_fill_market_order(order)
            elif order.order_type == OrderType.LIMIT:
                self._attempt_fill_limit_order(order)
        
    def on_order_event(self, event: OrderEvent):
        self._open_orders[event.order_id] = event
        logging.info(f"ExecutionHandler received and opened order {event.order_id} for {event.symbol} ({event.direction} {event.quantity}) at {event.timestamp.date()}")

    def _attempt_fill_market_order(self, order: OrderEvent):
        try:
            fill_price_data = self._latest_market_prices.get(order.symbol)

            if not fill_price_data:
                logging.warning(f"No market data available for {order.symbol} to fill order on {order.timestamp.date()}. Skipping fill.")
                self.push_failed_fill_event(order)
                return

            base_price = fill_price_data["price"]
            if order.direction == Signal.BUY:
                fill_price = base_price * (Decimal("1") + self.slippage_percent)
            elif order.direction == Signal.SELL:
                fill_price = base_price * (Decimal("1") - self.slippage_percent)
            else:
                fill_price = base_price 
            
            fill_price = max(Decimal("0.01"), fill_price) # Prevent zero or negative prices

            commission = (order.quantity * fill_price) * self.transaction_cost_percent
          
            self._create_and_push_fill_event(order, fill_price, successful=True, commission=commission)
            self._remove_order_from_open_orders(order.order_id)

        except Exception as e:
            logging.error(f"Error simulating order fill for {order.symbol} on {order.timestamp.date()}: {e}", exc_info=True)
            self.push_failed_fill_event(order)

    def _attempt_fill_limit_order(self, order: OrderEvent):
        """
        Attempts to fill a limit order.
        For a BUY (SELL) limit order, it can be filled 
        if the LOW (HIGH) price of the current bar is less (greater) or equal to the limit price.
        """
        try:
            fill_price_data = self._latest_market_prices.get(order.symbol)

            if not fill_price_data:
                logging.debug(f"No market data available for {order.symbol} to fill limit order {order.order_id} on {order.timestamp.date()}. Order remains open.")
                return
            
            can_fill = False
            fill_price = order.price

            if order.direction == Signal.BUY and fill_price_data["low"] <= order.price:
                can_fill = True
                fill_price = min(order.price, fill_price_data["close"])
            elif order.direction == Signal.SELL and fill_price_data["high"] >= order.price:
                can_fill = True
                fill_price = max(order.price, fill_price_data["close"])

            if can_fill:
                fill_price = max(Decimal("0.01"), fill_price)
                commission = (order.quantity * fill_price) * self.transaction_cost_percent
                
                self._create_and_push_fill_event(order, fill_price, successful=True, commission=commission)
                self._remove_order_from_open_orders(order.order_id)
            else:
                logging.debug(f"Limit order {order.order_id} for {order.symbol} ({order.direction} at {order.price:.2f}) not filled on {order.timestamp.date()}. Low: {fill_price_data['low']:.2f}, High: {fill_price_data['high']:.2f}")

        except Exception as e:
            logging.error(f"Error simulating limit order fill for {order.symbol} on {order.timestamp.date()} (Order ID: {order.order_id}): {e}", exc_info=True)
            self.push_failed_fill_event(order)
            
    def push_failed_fill_event(self, order: OrderEvent):
        self._create_and_push_fill_event(order, Decimal("0.0"), successful=False, commission=Decimal("0.0"))
        self._remove_order_from_open_orders(order.order_id)
    
    # HELPER METHOD 1: Handles creating, sending, and logging FillEvents
    def _create_and_push_fill_event(
        self, 
        order: OrderEvent, 
        fill_price: Decimal, 
        successful: bool, 
        commission: Decimal = Decimal("0.0")
    ):
        """
        Helper to create and put a FillEvent onto the queue, and log the outcome.
        """
        fill_event = FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            timestamp=order.timestamp,
            direction=order.direction,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            successful=successful
        )
        self.event_queue.put(fill_event)
        
        # Log based on success and order type
        if successful:
            log_message = (
                f"Filled {order.order_type.name} order {order.order_id}: "
                f"{order.direction.name} {order.quantity} of {order.symbol} at {fill_price:.2f} "
                f"(Commission: {commission:.2f})"
            )
            if order.order_type == OrderType.LIMIT:
                 log_message += f" (Limit: {order.price:.2f})" # Add limit price for context
            logging.info(f"{log_message} on {order.timestamp.date()}")
        else:
            logging.warning(f"Failed to fill order {order.order_id} for {order.symbol} on {order.timestamp.date()}.")

    # HELPER METHOD 2: Handles removing orders from the internal tracking dictionary
    def _remove_order_from_open_orders(self, order_id: str):
        """
        Helper to safely remove an order from the _open_orders dictionary.
        """
        if order_id in self._open_orders:
            del self._open_orders[order_id]
        else:
            logging.warning(f"Attempted to remove order {order_id} from _open_orders but it was not found. It might have been removed already.")
