from datetime import date, datetime
import logging
from typing import Dict, List, Optional
import pandas as pd
from alpheast.config.data_source import DataSource, DataSourceType, SupportedProvider
from alpheast.data.alpha_vantage_price_bar_client import AlphaVantageStdPriceBarClient
from alpheast.data.price_bar_client import PriceBarClient
from alpheast.events.event import DailyUpdateEvent, MarketEvent
from alpheast.events.event_queue import EventQueue
from alpheast.models.interval import Interval
from alpheast.models.price_bar import PriceBar


class DataHandler:
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
        data_source: DataSource,
    ):
        self.event_queue = event_queue
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval

        self.data_source = data_source
        self._load_data_from_data_source()

        self._all_data_df: pd.DataFrame = pd.DataFrame()

        self._df_iterator = None
        self._current_row_data = None
        self._has_more_data: bool = False

        self._last_processed_date: date = None
        self._last_processed_timestamp: Optional[datetime] = None

        logging.info(f"DataHandler initialized for symbols {symbols} from {start_date} to {end_date} with interval {interval.value}")
        self._preprocess_data()

    def stream_next_market_event(self):
        """
        Retrieves the next price bar(s), creates a MarketEvent and puts it onto the queue.
        Also pushes a DailyUpdateEvent when a new day begins.
        This function will now stream all events for a single timestamp in one go.
        """
        if not self.continue_backtest():
            logging.debug("No more data to stream.")
            return

        current_timestamp = None
        
        while self._has_more_data:
            row = self._current_row_data

            if current_timestamp is None:
                current_timestamp = row.timestamp
            elif row.timestamp > current_timestamp:
                break

            current_date = current_timestamp.date()

            if self._last_processed_date is None:
                self._last_processed_date = current_date
            elif current_date > self._last_processed_date:
                daily_update_event = DailyUpdateEvent(timestamp=datetime.combine(self._last_processed_date, datetime.min.time()))
                self.event_queue.put(daily_update_event)
                logging.debug(f"Pushed DailyUpdateEvent for {self._last_processed_date}")
                self._last_processed_date = current_date
            
            market_data = {
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume
            }

            market_event = MarketEvent(
                symbol=row.symbol,
                timestamp=row.timestamp,
                data=market_data
            )
            self.event_queue.put(market_event)
            logging.debug(f"Pushed MarketEvent for {row.symbol} on {row.timestamp}")
            
            self._load_next_row()

        if not self.continue_backtest() and self._last_processed_date is not None:
            daily_update_event = DailyUpdateEvent(timestamp=datetime.combine(self._last_processed_date, datetime.min.time()))
            self.event_queue.put(daily_update_event)
            logging.debug(f"Pushed final DailyUpdateEvent for {self._last_processed_date}")
            self._last_processed_date = None
            
    def continue_backtest(self) -> bool:
        return self._has_more_data

    def _preprocess_data(self):
        """
        Loads data for all specified symbols and interval, sorts it,
        and prepares a direct iterator over the DataFrame's rows.
        """
        all_rows_data = []
        for symbol in self.symbols:
            price_bars = self.price_bar_data[symbol]

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
            self._has_more_data = False
            return

        self._all_data_df = pd.DataFrame(all_rows_data)
        self._all_data_df = self._all_data_df.sort_values(by=["timestamp", "symbol"]).reset_index(drop=True)

        self._df_iterator = self._all_data_df.itertuples(index=False)

        self._load_next_row()

        logging.info(f"Loaded data for {len(self.symbols)} symbols across {len(self._all_data_df['timestamp'].unique())} unique timestamps.")

    def _load_next_row(self):
        """
        Loads the next row of data from the DataFrame iterator.
        Sets _has_more_data to False if no more rows.
        """
        try:
            self._current_row_data = next(self._df_iterator)
            self._has_more_data = True
        except StopIteration:
            self._current_row_data = None
            self._has_more_data = False
            logging.debug("No more rows available from data handler.")


    def _load_data_from_data_source(self):
        price_bar_data: Dict[str, List[PriceBar]] = {}
        type = self.data_source.type

        if type == DataSourceType.DIRECT:
            price_bar_data = self.data_source.price_bar_data
            if price_bar_data is None:
                raise ValueError("The provided price bar data is None, stopping backtest.")
        elif type == DataSourceType.CUSTOM_CLIENT:
            if self.data_source.custom_client is None:
                raise ValueError("The provided Custom Data Client is None, stopping backtest.")

            price_bar_data = self._load_all_symbols(self.data_source.custom_client)
        elif type == DataSourceType.STD_CLIENT:
            if self.data_source.api_key is None:
                raise ValueError("The provided API Key is None, stopping backtest.")
            if self.data_source.provider is None:
                raise ValueError("The provided Data Provider is None, stopping backtest.")

            match self.data_source.provider:
                case SupportedProvider.ALPHA_VANTAGE:
                    data_client = AlphaVantageStdPriceBarClient(self.data_source.api_key)
                case _:
                    raise ValueError("The provided Data Provider is not yet supported, stopping backtest.")

            price_bar_data = self._load_all_symbols(data_client)

        self.price_bar_data = price_bar_data

    def _load_all_symbols(self, client: PriceBarClient):
        price_bar_data: Dict[str, List[PriceBar]] = {}

        for symbol in self.symbols:
            symbol_data = client.get_price_bar_data(symbol, self.start_date, self.end_date, self.interval)
            price_bar_data[symbol] = symbol_data

        return price_bar_data