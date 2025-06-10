

from datetime import datetime
from decimal import Decimal, getcontext
import logging
from unittest.mock import Mock, patch

import pytest
from pytest_mock import mocker

from alpheast.events.event import FillEvent, MarketEvent, OrderEvent, SignalEvent
from alpheast.events.event_enums import OrderType
from alpheast.events.event_queue import EventQueue
from alpheast.models.signal import Signal
from alpheast.portfolio.benchmark_calculator import BenchmarkCalculator
from alpheast.portfolio.portfolio import Portfolio
from alpheast.portfolio.portfolio_manager import PortfolioManager
from alpheast.position_sizing.base_position_sizing import BasePositionSizing


getcontext().prec = 10

@pytest.fixture
def mock_event_queue():
    return Mock(spec=EventQueue)

@pytest.fixture
def mock_portfolio_account():
    mock_portfolio = Mock(spec=Portfolio)
    mock_portfolio.cash = Decimal("100000.0")
    mock_portfolio.initial_cash = Decimal("100000.0")
    mock_portfolio.holdings = {"GOOG": Decimal("10")}
    mock_portfolio.transaction_cost_percent = Decimal("0.001")
    mock_portfolio.get_holding_quantity.side_effect = lambda s: mock_portfolio.holdings.get(s, Decimal("0"))
    mock_portfolio.get_total_value.return_value = Decimal("100000.0")
    mock_portfolio.can_buy.return_value = True
    return mock_portfolio

@pytest.fixture
def mock_position_sizing_method():
    mock_method = Mock(spec=BasePositionSizing)
    mock_method.calculate_quantity.return_value = Decimal("10")
    return mock_method

@pytest.fixture
def mock_benchmark_calculator():
    mock_calculator = Mock(spec=BenchmarkCalculator)
    mock_calculator.is_initialized.return_value = True
    mock_calculator.get_daily_values.return_value = []
    return mock_calculator

@pytest.fixture
def portfolio_manager(mock_event_queue, mock_portfolio_account, mock_position_sizing_method, mock_benchmark_calculator):
    with patch("alpheast.portfolio.portfolio_manager.Portfolio", return_value=mock_portfolio_account):
        with patch("alpheast.portfolio.portfolio_manager.BenchmarkCalculator", return_value=mock_benchmark_calculator):
            pm = PortfolioManager(
                event_queue=mock_event_queue,
                symbols=["AAPL", "MSFT"],
                initial_cash=100_000.0,
                position_sizing_method=mock_position_sizing_method
            )
            pm.portfolio_account = mock_portfolio_account
            pm.benchmark_calculator = mock_benchmark_calculator
            return pm

# -- Tests ---
def test_initialization(portfolio_manager, mock_event_queue, mock_portfolio_account, mock_position_sizing_method, mock_benchmark_calculator):
    """Test that PortfolioManager initializes correctly with mocked dependencies."""
    assert portfolio_manager.event_queue == mock_event_queue
    assert portfolio_manager.portfolio_account == mock_portfolio_account
    assert portfolio_manager._latest_market_prices == {}
    assert portfolio_manager._current_date is None
    assert portfolio_manager._daily_values == []
    assert portfolio_manager._trade_log == []
    assert portfolio_manager.position_sizing_method == mock_position_sizing_method
    assert portfolio_manager.symbols == ["AAPL", "MSFT"]
    assert portfolio_manager.benchmark_calculator == mock_benchmark_calculator
    assert portfolio_manager._pending_orders == {}


def test_on_market_event(portfolio_manager):
    """Test that on_market_event updates latest market prices."""
    market_event = MarketEvent("AAPL", datetime(2023, 1, 1), {"close": 150.0})
    portfolio_manager.on_market_event(market_event)
    assert portfolio_manager._latest_market_prices["AAPL"] == Decimal("150.0")

    market_event_msft = MarketEvent("MSFT", datetime(2023, 1, 1), {"close": 250.0})
    portfolio_manager.on_market_event(market_event_msft)
    assert portfolio_manager._latest_market_prices["MSFT"] == Decimal("250.0")

def test_on_signal_event_no_market_data(portfolio_manager, caplog):
    """Test signal event with no market data available for the symbol."""
    signal_event = SignalEvent("GOOG", datetime(2023, 1, 1), Signal.BUY)
    with caplog.at_level(logging.WARNING):
        portfolio_manager.on_signal_event(signal_event)
        assert "No market data available yet" in caplog.text
    portfolio_manager.event_queue.put.assert_not_called()

def test_on_signal_event_buy_new_position_sufficient_cash(portfolio_manager, mock_event_queue, mock_position_sizing_method, mock_portfolio_account):
    """Test a successful buy signal for a new position with sufficient cash."""
    test_date = datetime(2023, 1, 1)
    portfolio_manager._latest_market_prices["AAPL"] = Decimal("150.0")
    mock_portfolio_account.get_holding_quantity.return_value = Decimal("0")
    mock_portfolio_account.cash = Decimal("10000.0")
    mock_position_sizing_method.calculate_quantity.return_value = Decimal("5")

    signal_event = SignalEvent("AAPL", test_date, Signal.BUY)
    portfolio_manager.on_signal_event(signal_event)

    mock_position_sizing_method.calculate_quantity.assert_called_once_with(
        symbol="AAPL",
        direction=Signal.BUY,
        current_price=Decimal("150.0"),
        portfolio_cash=Decimal("10000.0"),
        portfolio_holdings=mock_portfolio_account.holdings,
        portfolio_current_value=mock_portfolio_account.get_total_value.return_value,
        latest_market_prices={"AAPL": Decimal("150.0")}
    )

    mock_event_queue.put.assert_called_once()
    placed_order = mock_event_queue.put.call_args[0][0]
    assert isinstance(placed_order, OrderEvent)
    assert placed_order.symbol == "AAPL"
    assert placed_order.direction == Signal.BUY
    assert placed_order.quantity == Decimal("5")
    assert placed_order.price == Decimal("150.0")

    assert placed_order.order_id in portfolio_manager._pending_orders
    assert portfolio_manager._pending_orders[placed_order.order_id] == placed_order

def test_on_signal_event_buy_insufficient_cash(portfolio_manager, mock_event_queue, mock_portfolio_account, mock_position_sizing_method, caplog):
    """Test buy signal when calculated quantity and price exceed available cash."""
    test_date = datetime(2023, 1, 1)
    portfolio_manager._latest_market_prices["AAPL"] = Decimal("150.0")
    mock_portfolio_account.get_holding_quantity.return_value = Decimal("0")
    mock_portfolio_account.cash = Decimal("100.0")
    mock_position_sizing_method.calculate_quantity.return_value = Decimal("5")

    signal_event = SignalEvent("AAPL", test_date, Signal.BUY)
    with caplog.at_level(logging.WARNING):
        portfolio_manager.on_signal_event(signal_event)
        assert "Not enough cash to BUY" in caplog.text

    mock_event_queue.put.assert_not_called()

def test_on_signal_event_buy_zero_calculated_quantity(portfolio_manager, mock_event_queue, mock_portfolio_account, mock_position_sizing_method, caplog):
    """Test buy signal when position sizing returns zero quantity."""
    test_date = datetime(2023, 1, 1)
    portfolio_manager._latest_market_prices["AAPL"] = Decimal("150.0")
    mock_portfolio_account.get_holding_quantity.return_value = Decimal("0")
    mock_position_sizing_method.calculate_quantity.return_value = Decimal("0")

    signal_event = SignalEvent("AAPL", test_date, Signal.BUY)
    with caplog.at_level(logging.WARNING):
        portfolio_manager.on_signal_event(signal_event)
        assert "Calculated quantity for AAPL is 0" in caplog.text

    mock_event_queue.put.assert_not_called()

def test_on_signal_event_sell_existing_position(portfolio_manager, mock_event_queue, mock_portfolio_account):
    """Test a successful sell signal for an existing position."""
    test_date = datetime(2023, 1, 1)
    portfolio_manager._latest_market_prices["GOOG"] = Decimal("1000.0")
    mock_portfolio_account.holdings = {"GOOG": Decimal("5")}
    mock_portfolio_account.get_holding_quantity.return_value = Decimal("5")

    signal_event = SignalEvent("GOOG", test_date, Signal.SELL)
    portfolio_manager.on_signal_event(signal_event)

    mock_event_queue.put.assert_called_once()
    placed_order = mock_event_queue.put.call_args[0][0]
    assert isinstance(placed_order, OrderEvent)
    assert placed_order.symbol == "GOOG"
    assert placed_order.direction == Signal.SELL
    assert placed_order.quantity == Decimal("5")
    assert placed_order.price == Decimal("1000.0")

    assert placed_order.order_id in portfolio_manager._pending_orders

def test_on_fill_event_successful_buy(portfolio_manager, mock_portfolio_account):
    """Test processing a successful buy fill event."""
    order_id = "buy-order-123"
    test_date = datetime(2023, 1, 5)
    
    pending_order = OrderEvent(order_id, "AAPL", test_date, Signal.BUY, Decimal("5"), OrderType.MARKET, Decimal("150.0"))
    portfolio_manager._pending_orders[order_id] = pending_order

    fill_event = FillEvent(order_id, "AAPL", test_date, Signal.BUY, Decimal("5"), Decimal("150.5"), Decimal("0.75"), successful=True)
    portfolio_manager.on_fill_event(fill_event)

    mock_portfolio_account.buy.assert_called_once_with(
        symbol="AAPL",
        quantity=Decimal("5"),
        price=Decimal("150.5"),
        timestamp=test_date,
        commission=Decimal("0.75")
    )
    assert order_id not in portfolio_manager._pending_orders
    assert len(portfolio_manager._trade_log) == 1
    assert portfolio_manager._trade_log[0]["direction"] == Signal.BUY

def test_on_fill_event_successful_sell(portfolio_manager, mock_portfolio_account):
    """Test processing a successful sell fill event."""
    order_id = "sell-order-456"
    test_date = datetime(2023, 1, 6)

    pending_order = OrderEvent(order_id, "GOOG", test_date, Signal.SELL, Decimal("3"), OrderType.MARKET, Decimal("1000.0"))
    portfolio_manager._pending_orders[order_id] = pending_order

    fill_event = FillEvent(order_id, "GOOG", test_date, Signal.SELL, Decimal("3"), Decimal("999.5"), Decimal("2.0"), successful=True)
    portfolio_manager.on_fill_event(fill_event)

    mock_portfolio_account.sell.assert_called_once_with(
        symbol="GOOG",
        quantity=Decimal("3"),
        price=Decimal("999.5"),
        timestamp=test_date,
        commission=Decimal("2.0")
    )
    assert order_id not in portfolio_manager._pending_orders
    assert len(portfolio_manager._trade_log) == 1
    assert portfolio_manager._trade_log[0]["direction"] == Signal.SELL

def test_on_fill_event_unsuccessful(portfolio_manager, mock_portfolio_account, caplog):
    """Test processing an unsuccessful fill event."""
    order_id = "unsuccessful-order-789"
    test_date = datetime(2023, 1, 7)
    
    pending_order = OrderEvent(order_id, "MSFT", test_date, Signal.BUY, Decimal("10"), OrderType.MARKET, Decimal("200.0"))
    portfolio_manager._pending_orders[order_id] = pending_order

    fill_event = FillEvent(order_id, "MSFT", test_date, Signal.BUY, Decimal("10"), Decimal("200.0"), Decimal("0.0"), successful=False)
    with caplog.at_level(logging.WARNING):
        portfolio_manager.on_fill_event(fill_event)
        assert "Fill for MSFT on 2023-01-07 was not successful" in caplog.text

    mock_portfolio_account.buy.assert_not_called()
    mock_portfolio_account.sell.assert_not_called()
    assert order_id not in portfolio_manager._pending_orders
    assert len(portfolio_manager._trade_log) == 0

def test_on_signal_event_buy_with_pending_order_deduction(portfolio_manager, mock_event_queue, mock_portfolio_account, mock_position_sizing_method):
    """
    Test that cash available for new orders correctly accounts for pending buy orders.
    """
    test_date = datetime(2023, 1, 10)
    
    portfolio_manager._latest_market_prices["AAPL"] = Decimal("100.0")
    portfolio_manager._latest_market_prices["MSFT"] = Decimal("200.0")

    mock_portfolio_account.get_holding_quantity.return_value = Decimal("0")
    mock_portfolio_account.cash = Decimal("10000.0") # Initial cash
    mock_portfolio_account.transaction_cost_percent = Decimal("0.001")

    pending_order_id = "pending-msft-buy"
    pending_order = OrderEvent(pending_order_id, "MSFT", test_date, Signal.BUY, Decimal("10"), OrderType.MARKET, Decimal("200.0"))
    portfolio_manager._pending_orders[pending_order_id] = pending_order

    mock_position_sizing_method.calculate_quantity.return_value = Decimal("5")
    
    signal_event = SignalEvent("AAPL", test_date, Signal.BUY)
    portfolio_manager.on_signal_event(signal_event)

    # Expected cash available: 10000 - (10 * 200 * (1 + 0.001)) = 10000 - 2002 = 7998
    expected_cash_available = Decimal("7998.0") 

    mock_position_sizing_method.calculate_quantity.assert_called_once_with(
        symbol="AAPL",
        direction=Signal.BUY,
        current_price=Decimal("100.0"),
        portfolio_cash=expected_cash_available,
        portfolio_holdings=mock_portfolio_account.holdings,
        portfolio_current_value=mock_portfolio_account.get_total_value.return_value,
        latest_market_prices={"AAPL": Decimal("100.0"), "MSFT": Decimal("200.0")}
    )
    
    mock_event_queue.put.assert_called_once()
    placed_order = mock_event_queue.put.call_args[0][0]
    assert placed_order.symbol == "AAPL"
    assert placed_order.quantity == Decimal("5")
    assert placed_order.price == Decimal("100.0")
    assert placed_order.direction == Signal.BUY
