from datetime import datetime
import json
from typing import Any, Dict
from alpheast.config.backtest_config import BacktestingOptions
from alpheast.models.interval import Interval


class ConfigLoader:
    """
    Utility class to load backtest configurations from a JSON file.
    """

    @staticmethod
    def load_backtest_config_from_json(filepath: str) -> BacktestingOptions:
        """
        Loads backtest configuration from a JSON file.

        Args:
            filepath (str): The path to the JSON configuration file.

        Returns:
            BacktestConfig: An instance of BacktestConfig populated from the file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
            ValueError: If the JSON content is missing required fields or has invalid types.
        """
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON format in {filepath}: {e}", e.doc, e.pos)

        return ConfigLoader._parse_backtest_config_data(config_data)

    @staticmethod
    def _parse_backtest_config_data(data: Dict[str, Any]) -> BacktestingOptions:
        """
        Parses a dictionary into a BacktestConfig object, handling type conversions.
        """
        try:
            symbols = data["symbols"]
            start_date_str = data["start_date"]
            end_date_str = data["end_date"]
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            interval_str = data["interval"]
            if interval_str is not None:
                try:
                    interval = Interval[interval_str.upper()]
                except KeyError:
                    raise ValueError(f"Invalid interval: '{interval_str}'. Must be one of: {[e.name for e in Interval]}")
            initial_cash = float(data["initial_cash"])
            initial_cash = float(data["initial_cash"])
            transaction_cost_percent = float(data.get("transaction_cost_percent")) if data.get("transaction_cost_percent") is not None else None
            slippage_percent = float(data.get("slippage_percent")) if data.get("slippage_percent") is not None else None

            return BacktestingOptions(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                initial_cash=initial_cash,
                transaction_cost_percent=transaction_cost_percent,
                slippage_percent=slippage_percent
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error parsing backtest config data: {e}")
