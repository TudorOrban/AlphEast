import json
import re
import pytest
from datetime import date
from unittest.mock import mock_open

from alpheast.config.config_loader import ConfigLoader
from alpheast.config.backtest_config import BacktestingOptions # Assuming this structure
from alpheast.models.interval import Interval


def test_load_backtest_config_from_json_success(mocker):
    """
    Test successful loading of a valid JSON configuration file.
    This test assumes all fields are present and correctly formatted as expected by the ConfigLoader.
    """
    mock_config_data = {
        "symbols": ["AAPL", "MSFT"],
        "start_date": "2020-01-01",
        "end_date": "2021-12-31",
        "interval": "DAILY",
        "initial_cash": 100000.0,
        "transaction_cost_percent": 0.001,
        "slippage_percent": 0.0005
    }
    mocker.patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data)))

    config = ConfigLoader.load_backtest_config_from_json("dummy_path.json")

    assert isinstance(config, BacktestingOptions)
    assert config.symbols == ["AAPL", "MSFT"]
    assert config.start_date == date(2020, 1, 1)
    assert config.end_date == date(2021, 12, 31)
    assert config.interval == Interval.DAILY
    assert config.initial_cash == 100000.0
    assert config.transaction_cost_percent == 0.001
    assert config.slippage_percent == 0.0005

def test_load_backtest_config_from_json_no_optional_fields(mocker):
    """
    Test successful loading when optional fields (transaction_cost_percent, slippage_percent) are None or missing.
    The original ConfigLoader defaults to None if the key is not present or if the value is None.
    """
    mock_config_data = {
        "symbols": ["GOOG"],
        "start_date": "2022-01-01",
        "end_date": "2022-12-31",
        "interval": "WEEKLY",
        "initial_cash": 50000.0
    }
    mocker.patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data)))

    config = ConfigLoader.load_backtest_config_from_json("dummy_path.json")

    assert isinstance(config, BacktestingOptions)
    assert config.symbols == ["GOOG"]
    assert config.start_date == date(2022, 1, 1)
    assert config.end_date == date(2022, 12, 31)
    assert config.interval == Interval.WEEKLY
    assert config.initial_cash == 50000.0
    assert config.transaction_cost_percent is None
    assert config.slippage_percent is None        

def test_load_backtest_config_from_json_file_not_found(mocker):
    """
    Test FileNotFoundError is raised when the config file doesn't exist.
    """
    mocker.patch('builtins.open', side_effect=FileNotFoundError)

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        ConfigLoader.load_backtest_config_from_json("non_existent_file.json")

def test_load_backtest_config_from_json_invalid_json(mocker):
    """
    Test json.JSONDecodeError is raised for invalid JSON content.
    """
    mocker.patch('builtins.open', mock_open(read_data='{"symbols": ["AAPL",}')) # Malformed JSON

    with pytest.raises(json.JSONDecodeError, match="Invalid JSON format"):
        ConfigLoader.load_backtest_config_from_json("invalid.json")

@pytest.mark.parametrize("missing_field", [
    "symbols",
    "start_date",
    "end_date",
    "interval",
    "initial_cash"
])
def test_parse_backtest_config_data_missing_required_field_keyerror(missing_field):
    """
    Test KeyError is raised when a required field is missing in the data dictionary,
    matching the original ConfigLoader's behavior.
    """
    base_config = {
        "symbols": ["AAPL"],
        "start_date": "2020-01-01",
        "end_date": "2021-12-31",
        "interval": "DAILY",
        "initial_cash": 100000.0,
        "transaction_cost_percent": 0.001,
        "slippage_percent": 0.0005
    }
    del base_config[missing_field] 
    
    with pytest.raises(KeyError) as excinfo:
        ConfigLoader._parse_backtest_config_data(base_config)
    assert str(excinfo.value) == f"'{missing_field}'"

@pytest.mark.parametrize("invalid_field, invalid_value, expected_exception, expected_match", [
    ("start_date", "not-a-date", ValueError, "time data 'not-a-date' does not match format '%Y-%m-%d'"),
    ("end_date", "2021/12/31", ValueError, "time data '2021/12/31' does not match format '%Y-%m-%d'"),
    ("interval", "INVALID_INTERVAL", ValueError, "Invalid interval: 'INVALID_INTERVAL'"), 
    ("initial_cash", "not_a_number", ValueError, "could not convert string to float: 'not_a_number'"),
    ("interval", 123, AttributeError, "'int' object has no attribute 'upper'"),
    ("transaction_cost_percent", "invalid_cost", ValueError, "could not convert string to float: 'invalid_cost'"),
    ("slippage_percent", {}, ValueError, re.escape("Error parsing backtest config data: float() argument must be a string or a real number, not 'dict'"))
])
def test_parse_backtest_config_data_invalid_type_or_format(invalid_field, invalid_value, expected_exception, expected_match):
    """
    Test that appropriate exceptions (ValueError, AttributeError, TypeError) are raised
    for invalid types or formats, matching the original ConfigLoader's behavior.
    """
    config_data = {
        "symbols": ["AAPL"],
        "start_date": "2020-01-01",
        "end_date": "2021-12-31",
        "interval": "DAILY",
        "initial_cash": 100000.0,
        "transaction_cost_percent": 0.001,
        "slippage_percent": 0.0005
    }
    config_data[invalid_field] = invalid_value

    with pytest.raises(expected_exception, match=expected_match):
        ConfigLoader._parse_backtest_config_data(config_data)

def test_load_backtest_config_from_json_empty_dates(mocker):
    """
    Test successful loading when start_date and end_date are None in JSON.
    """
    mock_config_data = {
        "symbols": ["SPY"],
        "start_date": None,
        "end_date": None,
        "interval": "MONTHLY",
        "initial_cash": 200000.0,
        "transaction_cost_percent": 0.002,
        "slippage_percent": 0.001
    }
    mocker.patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data)))

    config = ConfigLoader.load_backtest_config_from_json("dummy_path_empty_dates.json")

    assert isinstance(config, BacktestingOptions)
    assert config.symbols == ["SPY"]
    assert config.start_date is None
    assert config.end_date is None
    assert config.interval == Interval.MONTHLY
    assert config.initial_cash == 200000.0
    assert config.transaction_cost_percent == 0.002
    assert config.slippage_percent == 0.001