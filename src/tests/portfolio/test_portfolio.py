
from datetime import datetime
from decimal import Decimal, getcontext

import pytest

from alpheast.portfolio.portfolio import Portfolio


getcontext().prec = 10

@pytest.fixture
def portfolio():
    return Portfolio(initial_cash=10000.0, transaction_cost_percent=Decimal("0.001"))

def test_portfoilio_initialization(portfolio):
    assert portfolio.cash == Decimal("10000.0")
    assert portfolio.initial_cash == Decimal("10000.0")
    assert portfolio.holdings == {}
    assert portfolio.transaction_cost_percent == Decimal("0.001")
    assert portfolio.daily_values == []
    assert portfolio.trade_log == []

def test_portfolio_initialization_invalid_cash():
    with pytest.raises(ValueError, match="Initial cash must be positive."):
        Portfolio(initial_cash=0.0)
    with pytest.raises(ValueError, match="Initial cash must be positive."):
        Portfolio(initial_cash=-100.0)

def test_get_holding_quantity(portfolio):
    assert portfolio.get_holding_quantity("AAPL") == Decimal("0")
    portfolio.holdings["AAPL"] = Decimal("50")
    assert portfolio.get_holding_quantity("AAPL") == Decimal("50")


def test_can_buy_sufficient_cash(portfolio):
    # Price: 100, Quantity: 10, Trade cost: 1000. Total cost: 1000 + (1000 * 0.001) = 1001
    assert portfolio.can_buy(price=Decimal("100"), quantity=Decimal("10")) is True

def test_can_buy_insufficient_cash(portfolio):
    # Price: 1000, Quantity: 11, Trade cost: 11000. Total cost: 11000 + (11000 * 0.001) = 11011
    assert portfolio.can_buy(price=Decimal("1000"), quantity=Decimal("11")) is False

def test_buy_successful(portfolio):
    initial_cash = portfolio.cash
    symbol = "AAPL"
    quantity = Decimal("10")
    price = Decimal("150.0")
    commission = Decimal("1.5") 
    timestamp = datetime(2023, 1, 1, 9, 30)

    portfolio.buy(symbol, quantity, price, timestamp, commission)

    expected_cash = initial_cash - (quantity * price) - commission
    assert portfolio.cash == expected_cash
    assert portfolio.cash == Decimal("10000.0") - Decimal("1500.0") - Decimal("1.5")

    assert portfolio.holdings[symbol] == quantity

    assert len(portfolio.trade_log) == 1
    logged_trade = portfolio.trade_log[0]
    assert logged_trade["symbol"] == symbol
    assert logged_trade["type"] == "BUY"
    assert logged_trade["quantity"] == quantity
    assert logged_trade["price"] == price
    assert logged_trade["commission"] == commission
    assert logged_trade["total_cost"] == (quantity * price) + commission
    assert logged_trade["cash_after_trade"] == portfolio.cash

def test_buy_insufficient_cash_raises_error(portfolio):
    symbol = "MSFT"
    quantity = Decimal("100")
    price = Decimal("200.0") 
    timestamp = datetime(2023, 1, 2)
    
    with pytest.raises(ValueError, match="Insufficient cash to perform buy operation"):
        portfolio.buy(symbol, quantity, price, timestamp, Decimal("5.0"))


def test_sell_successful(portfolio):
    portfolio.buy("GOOG", Decimal("20"), Decimal("100.0"), datetime(2023, 1, 1), Decimal("2.0"))
    initial_cash_after_buy = portfolio.cash
    
    symbol = "GOOG"
    quantity = Decimal("10")
    price = Decimal("110.0")
    commission = Decimal("1.0")
    timestamp = datetime(2023, 1, 5, 10, 0)

    portfolio.sell(symbol, quantity, price, timestamp, commission)

    expected_cash = initial_cash_after_buy + (quantity * price) - commission
    assert portfolio.cash == expected_cash
    
    assert portfolio.holdings[symbol] == Decimal("10")

    assert len(portfolio.trade_log) == 2 
    logged_sell_trade = portfolio.trade_log[1]
    assert logged_sell_trade["symbol"] == symbol
    assert logged_sell_trade["type"] == "SELL"
    assert logged_sell_trade["quantity"] == quantity
    assert logged_sell_trade["price"] == price
    assert logged_sell_trade["commission"] == commission
    assert logged_sell_trade["total_revenue"] == (quantity * price) - commission
    assert logged_sell_trade["cash_after_trade"] == portfolio.cash

def test_sell_insufficient_holdings_raises_error(portfolio):
    symbol = "AMZN"
    quantity = Decimal("5")
    price = Decimal("100.0")
    timestamp = datetime(2023, 1, 3)

    with pytest.raises(ValueError, match="Insufficient holdings of AMZN to perform sell operation."):
        portfolio.sell(symbol, quantity, price, timestamp)

    portfolio.buy(symbol, Decimal("3"), Decimal("100.0"), timestamp, Decimal("0.3"))
    with pytest.raises(ValueError, match="Insufficient holdings of AMZN to perform sell operation."):
        portfolio.sell(symbol, Decimal("5"), price, timestamp)

def test_get_total_value_alias(portfolio):
    portfolio.buy("XYZ", Decimal("5"), Decimal("100.0"), datetime(2023, 1, 1), Decimal("0.5"))
    current_prices = {"XYZ": Decimal("105.0")}
    assert portfolio.get_total_value(current_prices) == portfolio.get_current_value(current_prices)

def test_record_daily_value(portfolio):
    """Test recording of daily portfolio value and state."""
    portfolio.buy("DEF", Decimal("10"), Decimal("100.0"), datetime(2023, 1, 1), Decimal("1.0")) # Cash: 10000 - 1000 - 1 = 8999
    
    date = datetime(2023, 1, 2).date()
    current_prices = {"DEF": Decimal("105.0")}
    # Total value: 8999 (cash) + 1050 (holdings) = 10049

    portfolio.record_daily_value(date, current_prices)

    assert len(portfolio.daily_values) == 1
    daily_record = portfolio.daily_values[0]
    assert daily_record["date"] == date
    assert daily_record["total_value"] == float(Decimal("10049.0"))
    assert daily_record["cash"] == float(Decimal("8999.0"))
    assert daily_record["holdings"] == {"DEF": float(Decimal("10"))}

def test_get_summary(portfolio):
    """Test the portfolio summary."""
    portfolio.buy("GHI", Decimal("5"), Decimal("200.0"), datetime(2023, 1, 1), Decimal("1.0"))
    portfolio.sell("GHI", Decimal("2"), Decimal("210.0"), datetime(2023, 1, 2), Decimal("0.5"))

    summary = portfolio.get_summary()

    assert summary["initial_cash"] == float(Decimal("10000.0"))
    # Calculate expected final cash: 10000 - (5*200) - 1 + (2*210) - 0.5 = 10000 - 1000 - 1 + 420 - 0.5 = 9418.5
    assert summary["cash"] == float(Decimal("9418.5"))
    assert summary["holdings"] == {"GHI": float(Decimal("3"))}
    assert summary["total_trades"] == 2
