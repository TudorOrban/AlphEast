import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch
import logging

from alpheast.config.data_source import DataSource, DataSourceType, SupportedProvider
from alpheast.data.alpha_vantage_price_bar_client import AlphaVantageStdPriceBarClient
from alpheast.data.price_bar_client import PriceBarClient
from alpheast.events.event import DailyUpdateEvent, MarketEvent
from alpheast.events.event_queue import EventQueue
from alpheast.handlers.data_handler import DataHandler
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar

logging.basicConfig(level=logging.DEBUG)

# --- Fixtures ---
@pytest.fixture
def mock_event_queue():
    return Mock(spec=EventQueue)

@pytest.fixture
def mock_price_bar_client():
    mock_client = Mock(spec=PriceBarClient)
    def get_mock_price_bars(symbol, start, end, interval):
        if symbol == "AAPL":
            return [
                PriceBar("AAPL", datetime(2023, 1, 1, 9, 30), Decimal("100.0"), Decimal("101.0"), Decimal("99.0"), Decimal("100.5"), Decimal("100000")),
                PriceBar("AAPL", datetime(2023, 1, 2, 9, 30), Decimal("100.5"), Decimal("102.0"), Decimal("99.5"), Decimal("101.0"), Decimal("120000")),
                PriceBar("AAPL", datetime(2023, 1, 3, 9, 30), Decimal("101.0"), Decimal("103.0"), Decimal("100.0"), Decimal("102.5"), Decimal("150000")),
            ]
        elif symbol == "MSFT":
            return [
                PriceBar("MSFT", datetime(2023, 1, 1, 9, 30), Decimal("200.0"), Decimal("201.0"), Decimal("199.0"), Decimal("200.5"), Decimal("50000")),
                PriceBar("MSFT", datetime(2023, 1, 2, 9, 30), Decimal("200.5"), Decimal("202.0"), Decimal("199.5"), Decimal("201.0"), Decimal("60000")),
            ]
        return []
    mock_client.get_price_bar_data.side_effect = get_mock_price_bars
    return mock_client

@pytest.fixture
def mock_alpha_vantage_client():
    mock_client = Mock(spec=AlphaVantageStdPriceBarClient)
    def get_mock_price_bars_av(symbol, start, end, interval):
        if symbol == "GOOG":
            return [
                PriceBar("GOOG", datetime(2023, 1, 1, 9, 30), Decimal("150.0"), Decimal("151.0"), Decimal("149.0"), Decimal("150.5"), Decimal("80000")),
                PriceBar("GOOG", datetime(2023, 1, 2, 9, 30), Decimal("150.5"), Decimal("152.0"), Decimal("149.5"), Decimal("151.0"), Decimal("90000")),
            ]
        return []
    mock_client.get_price_bar_data.side_effect = get_mock_price_bars_av
    return mock_client


@pytest.fixture
def sample_direct_price_bar_data():
    return {
        "TSLA": [
            PriceBar("TSLA", datetime(2023, 1, 1, 9, 30), Decimal("300.0"), Decimal("301.0"), Decimal("299.0"), Decimal("300.5"), Decimal("200000")),
            PriceBar("TSLA", datetime(2023, 1, 2, 9, 30), Decimal("300.5"), Decimal("302.0"), Decimal("299.5"), Decimal("301.0"), Decimal("250000")),
        ],
        "AMZN": [
            PriceBar("AMZN", datetime(2023, 1, 1, 9, 30), Decimal("100.0"), Decimal("101.0"), Decimal("99.0"), Decimal("100.5"), Decimal("50000")),
        ]
    }


# --- Tests ---
def test_data_handler_init_direct_source(mock_event_queue, sample_direct_price_bar_data, caplog):
    """Test DataHandler initialization with DIRECT data source."""
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    symbols = ["TSLA", "AMZN"]
    data_source = DataSource(DataSourceType.DIRECT, price_bar_data=sample_direct_price_bar_data)

    with caplog.at_level(logging.INFO):
        handler = DataHandler(
            event_queue=mock_event_queue,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=Interval.DAILY,
            data_source=data_source
        )

    assert handler.event_queue == mock_event_queue
    assert handler.symbols == symbols
    assert handler.start_date == start_date
    assert handler.end_date == end_date
    assert handler.interval == Interval.DAILY
    assert handler.data_source == data_source
    assert "DataHandler initialized" in caplog.text
    assert "Loaded data for 2 symbols across 2 unique timestamps." in caplog.text

    assert not handler._all_data_df.empty


def test_data_handler_init_raises_value_error_if_direct_data_none(mock_event_queue):
    """Test ValueError if DIRECT data source has None price_bar_data."""
    data_source = DataSource(DataSourceType.DIRECT, price_bar_data=None)
    with pytest.raises(ValueError, match="The provided price bar data is None, stopping backtest."):
        DataHandler(
            event_queue=mock_event_queue,
            symbols=["TEST"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            interval=Interval.DAILY,
            data_source=data_source
        )

def test_data_handler_init_raises_value_error_if_custom_client_none(mock_event_queue):
    """Test ValueError if CUSTOM_CLIENT data source has None custom_client."""
    data_source = DataSource(DataSourceType.CUSTOM_CLIENT, custom_client=None)
    with pytest.raises(ValueError, match="The provided Custom Data Client is None, stopping backtest."):
        DataHandler(
            event_queue=mock_event_queue,
            symbols=["TEST"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            interval=Interval.DAILY,
            data_source=data_source
        )

def test_data_handler_init_raises_value_error_if_std_client_api_key_none(mock_event_queue):
    """Test ValueError if STD_CLIENT data source has None api_key."""
    data_source = DataSource(DataSourceType.STD_CLIENT, api_key=None, provider=SupportedProvider.ALPHA_VANTAGE)
    with pytest.raises(ValueError, match="The provided API Key is None, stopping backtest."):
        DataHandler(
            event_queue=mock_event_queue,
            symbols=["TEST"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            interval=Interval.DAILY,
            data_source=data_source
        )

def test_data_handler_init_raises_value_error_if_std_client_provider_none(mock_event_queue):
    """Test ValueError if STD_CLIENT data source has None provider."""
    data_source = DataSource(DataSourceType.STD_CLIENT, api_key="key", provider=None)
    with pytest.raises(ValueError, match="The provided Data Provider is None, stopping backtest."):
        DataHandler(
            event_queue=mock_event_queue,
            symbols=["TEST"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            interval=Interval.DAILY,
            data_source=data_source
        )

def test_data_handler_init_raises_value_error_if_unsupported_provider(mock_event_queue):
    """Test ValueError if STD_CLIENT data source has an unsupported provider."""
    data_source = DataSource(DataSourceType.STD_CLIENT, api_key="key", provider=Mock()) 
    data_source.provider.name = "UNSUPPORTED"
    
    with pytest.raises(ValueError, match="The provided Data Provider is not yet supported, stopping backtest."):
        DataHandler(
            event_queue=mock_event_queue,
            symbols=["TEST"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            interval=Interval.DAILY,
            data_source=data_source
        )

def test_data_handler_stream_next_market_event_daily_update(mock_event_queue, mocker):
    """
    Test stream_next_market_event pushes DailyUpdateEvents and MarketEvents correctly
    over multiple days.
    """
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    symbols = ["AAPL", "MSFT"]

    # Prepare data that spans multiple days
    mock_price_bars = {
        "AAPL": [
            PriceBar("AAPL", datetime(2023, 1, 1, 9, 30), Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100.5"), Decimal("100000")),
            PriceBar("AAPL", datetime(2023, 1, 2, 9, 30), Decimal("101"), Decimal("102"), Decimal("100"), Decimal("101.5"), Decimal("110000")),
            PriceBar("AAPL", datetime(2023, 1, 3, 9, 30), Decimal("102"), Decimal("103"), Decimal("101"), Decimal("102.5"), Decimal("120000")),
        ],
        "MSFT": [
            PriceBar("MSFT", datetime(2023, 1, 1, 9, 30), Decimal("200"), Decimal("201"), Decimal("199"), Decimal("200.5"), Decimal("50000")),
            PriceBar("MSFT", datetime(2023, 1, 2, 9, 30), Decimal("201"), Decimal("202"), Decimal("200"), Decimal("201.5"), Decimal("60000")),
        ]
    }
    data_source = DataSource(DataSourceType.DIRECT, price_bar_data=mock_price_bars)

    handler = DataHandler(
        event_queue=mock_event_queue,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=Interval.DAILY,
        data_source=data_source
    )

    mock_event_queue.put.reset_mock()

    # Stream Day 1: 2023-01-01 (AAPL, MSFT)
    # Expected: 2 MarketEvents for Jan 1
    handler.stream_next_market_event()
    assert mock_event_queue.put.call_count == 2
    market_events_day1 = [call.args[0] for call in mock_event_queue.put.call_args_list if isinstance(call.args[0], MarketEvent)]
    assert len(market_events_day1) == 2
    assert any(me.symbol == "AAPL" and me.timestamp.date() == date(2023, 1, 1) for me in market_events_day1)
    assert any(me.symbol == "MSFT" and me.timestamp.date() == date(2023, 1, 1) for me in market_events_day1)
    mock_event_queue.put.reset_mock()

    # Stream Day 2: 2023-01-02 (AAPL, MSFT)
    # Expected: 1 DailyUpdateEvent for 2023-01-01, then 2 MarketEvents for 2023-01-02
    handler.stream_next_market_event()
    assert mock_event_queue.put.call_count == 3
    
    # Check for DailyUpdateEvent first
    daily_update_event_day1 = mock_event_queue.put.call_args_list[0].args[0]
    assert isinstance(daily_update_event_day1, DailyUpdateEvent)
    assert daily_update_event_day1.timestamp.date() == date(2023, 1, 1)

    # Check for MarketEvents
    market_events_day2 = [call.args[0] for call in mock_event_queue.put.call_args_list[1:] if isinstance(call.args[0], MarketEvent)]
    assert len(market_events_day2) == 2
    assert any(me.symbol == "AAPL" and me.timestamp.date() == date(2023, 1, 2) for me in market_events_day2)
    assert any(me.symbol == "MSFT" and me.timestamp.date() == date(2023, 1, 2) for me in market_events_day2)
    mock_event_queue.put.reset_mock()

    # Stream Day 3: 2023-01-03 (Only AAPL)
    # Expected: 1 DailyUpdateEvent for 2023-01-02, then 1 MarketEvent for 2023-01-03
    handler.stream_next_market_event()
    assert mock_event_queue.put.call_count == 3
    
    daily_update_event_day2 = mock_event_queue.put.call_args_list[0].args[0]
    assert isinstance(daily_update_event_day2, DailyUpdateEvent)
    assert daily_update_event_day2.timestamp.date() == date(2023, 1, 2)

    market_event_day3 = mock_event_queue.put.call_args_list[1].args[0]
    assert isinstance(market_event_day3, MarketEvent)
    assert market_event_day3.symbol == "AAPL"
    assert market_event_day3.timestamp.date() == date(2023, 1, 3)

def test_data_handler_continue_backtest(mock_event_queue, sample_direct_price_bar_data):
    """Test continue_backtest method."""
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    symbols = ["TSLA", "AMZN"]
    data_source = DataSource(DataSourceType.DIRECT, price_bar_data=sample_direct_price_bar_data)

    handler = DataHandler(
        event_queue=mock_event_queue,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=Interval.DAILY,
        data_source=data_source
    )

    assert handler.continue_backtest() is True

    handler.stream_next_market_event()
    assert handler.continue_backtest() is True
    handler.stream_next_market_event()
    assert handler.continue_backtest() is False

    # After all data is streamed
    handler.stream_next_market_event()
    assert handler.continue_backtest() is False

def test_data_handler_load_all_symbols(mock_event_queue, mock_price_bar_client):
    """Test _load_all_symbols method directly."""
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    symbols = ["AAPL", "MSFT"]
    interval = Interval.DAILY

    data_source = DataSource(DataSourceType.CUSTOM_CLIENT, custom_client=mock_price_bar_client)
    handler = DataHandler(
        event_queue=mock_event_queue,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        data_source=data_source
    )
    
    # Now call the internal method
    loaded_data = handler._load_all_symbols(mock_price_bar_client)

    assert "AAPL" in loaded_data
    assert "MSFT" in loaded_data
    assert len(loaded_data["AAPL"]) == 3
    assert len(loaded_data["MSFT"]) == 2
    mock_price_bar_client.get_price_bar_data.assert_any_call("AAPL", start_date, end_date, interval)
    mock_price_bar_client.get_price_bar_data.assert_any_call("MSFT", start_date, end_date, interval)