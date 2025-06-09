
from datetime import date, datetime
import logging
from typing import Dict, List, Optional
import pandas as pd
from alpheast.models.input_data import PriceBar
from alpheast.models.event import DailyUpdateEvent, MarketEvent
from alpheast.event_queue import EventQueue
from alpheast.handlers.data_handler import DataHandler
from alpheast.data.price_bars.interval import Interval
from alpheast.data.sources.financial_data_client import FinancialDataClient


class DatabaseDataHandler(DataHandler):
    """
    A concrete data handler that fetches price data from the database
    via DatabaseDataRepository for a specified interval.
    Also pushes DailyUpdateEvents.
    """
    def __init__(
        self, 
        event_queue: EventQueue, 
        symbols: List[str], 
        start_date: date, 
        end_date: date,
        interval: Interval,
        price_data: Dict[str, List[PriceBar]],
        data_client: Optional[FinancialDataClient] = None
    ):
        self.event_queue = event_queue
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.price_data = price_data
        
        self._all_data_df: pd.DataFrame = pd.DataFrame()
        self._unique_timestamps: List[datetime] = []
        self._current_timestamp_idx: int = 0
        self._last_processed_date: date = None
        
        logging.info(
            f"DatabaseDataHandler initialized for symbols {symbols} from {start_date} to {end_date} "
            f"with interval {interval.value}"
        )
        self._load_all_data()

    def stream_next_market_event(self):
        """
        Retrieves the next price bar(s), creates a MarketEvent and puts it onto the queue.
        Also pushes a DailyUpdateEvent when a new day begins.
        """
        if not self.continue_backtest():
            logging.debug("No more data to stream.")
            return
        
        current_timestamp_obj = self._unique_timestamps[self._current_timestamp_idx]
        current_interval_data = self._all_data_df[self._all_data_df["timestamp"] == current_timestamp_obj]
        current_date = current_timestamp_obj.date()

        if self._last_processed_date is None:
            self._last_processed_date = current_date
        elif current_date > self._last_processed_date:
            daily_update_event = DailyUpdateEvent(timestamp=datetime.combine(self._last_processed_date, datetime.min.time()))
            self.event_queue.put(daily_update_event)
            logging.debug(f"Pushed DailyUpdateEvent for {self._last_processed_date}")
            self._last_processed_date = current_date
            
        for _, row in current_interval_data.iterrows():
            market_data = {
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"]
            }

            market_event = MarketEvent(
                symbol=row["symbol"],
                timestamp=row["timestamp"], 
                data=market_data
            )
            self.event_queue.put(market_event)
            logging.debug(f"Pushed MarketEvent for {row['symbol']} on {row['timestamp']}")

        self._current_timestamp_idx += 1

        if not self.continue_backtest():
            daily_update_event = DailyUpdateEvent(timestamp=datetime.combine(self._last_processed_date, datetime.min.time()))
            self.event_queue.put(daily_update_event)
            logging.debug(f"Pushed final DailyUpdateEvent for {self._last_processed_date}")

    def continue_backtest(self) -> bool:
        return self._current_timestamp_idx < len(self._unique_timestamps)

    def _load_all_data(self):
        """
        Loads data for all specified symbols and interval, and sorts it by timestamp and then by symbol.
        """
        all_rows_data = []
        for symbol in self.symbols:
            price_bars = self.price_data[symbol]

            for pb in price_bars:
                all_rows_data.append({
                    "timestamp": pb.timestamp,
                    "symbol": pb.symbol,
                    "open": float(pb.open), 
                    "high": float(pb.high),
                    "low": float(pb.low),
                    "close": float(pb.close),
                    "volume": float(pb.volume)
                })

        if not all_rows_data:
            logging.warning(f"No price data found for any of the symbols {self.symbols} at interval {self.interval.value}")
            return
        
        self._all_data_df = pd.DataFrame(all_rows_data)
        self._all_data_df = self._all_data_df.sort_values(by=["timestamp", "symbol"]).reset_index(drop=True)

        self._unique_timestamps = sorted(self._all_data_df["timestamp"].unique().tolist())
        logging.info(f"Loaded data for {len(self.symbols)} symbols across {len(self._unique_timestamps)} unique timestamps.")
