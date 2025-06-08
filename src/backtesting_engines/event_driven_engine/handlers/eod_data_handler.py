
from datetime import date, datetime
import logging
from typing import List

import pandas as pd
from src.data.eod_prices.model import EODPrice
from src.data.eod_prices.repository import EODPriceRepository
from src.backtesting_engines.event_driven_engine.models.event import DailyUpdateEvent, MarketEvent
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.handlers.data_handler import DataHandler


class EODDatabaseDataHandler(DataHandler):
    """
    A concrete data handler that fetches End-Of-Day (EOD) price data
    from the database via EODPriceRepository. Also pushes DailyUpdateEvents.
    """
    def __init__(self, event_queue: EventQueue, symbols: List[str], start_date: date, end_date: date):
        self.event_queue = event_queue
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.repository = EODPriceRepository()

        self._all_data_df: pd.DataFrame = pd.DataFrame()
        self._unique_dates: List[date] = []
        self._current_date_idx: int = 0

        logging.info(f"EODDatabaseDataHandler initialized for symbols {symbols} from {start_date} to {end_date}")
        self._load_all_data()

    def stream_next_market_event(self):
        """
        Retrieves the next EODPrice bar, creates a MarketEvent and puts it onto the queue
        """
        if not self.continue_backtest():
            logging.debug("No more EOD data to stream.")
            return
        
        current_date_obj = self._unique_dates[self._current_date_idx]
        daily_market_data = self._all_data_df[self._all_data_df["date"] == current_date_obj]
        
        current_datetime = datetime.combine(current_date_obj, datetime.min.time())

        for _, row in daily_market_data.iterrows():
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
            logging.debug(f"Pushed MarketEvent for {row['symbol']} on {row['date']}")

        daily_update_event = DailyUpdateEvent(timestamp=current_datetime)
        self.event_queue.put(daily_update_event)
        logging.debug(f"Pushed DailyUpdateEvent for {current_date_obj}")

        self._current_date_idx += 1

    def continue_backtest(self) -> bool:
        return self._current_date_idx < len(self._unique_dates)

    def _load_all_data(self):
        """
        Loads EOD data for all specified symbols and sorts it by date and then by symbol.
        """
        all_rows_data = []
        for symbol in self.symbols:
            logging.info(f"Fetching EOD data for {symbol}...")
            eod_prices = self.repository.get_eod_prices_by_symbol(
                symbol=symbol,
                start_date=self.start_date,
                end_date=self.end_date
            )
            for price_obj in eod_prices:
                all_rows_data.append({
                    "date": price_obj.time.date(),
                    "symbol": price_obj.symbol,
                    "open": float(price_obj.open),
                    "high": float(price_obj.high),
                    "low": float(price_obj.low),
                    "close": float(price_obj.close),
                    "volume": float(price_obj.volume),
                    "timestamp": price_obj.time
                })

        if not all_rows_data:
            logging.warning(f"No EOD prices found for any of the symbols {self.symbols}")
            return
        
        self._all_data_df = pd.DataFrame(all_rows_data)
        self._all_data_df = self._all_data_df.sort_values(by=["date", "symbol"]).reset_index(drop=True)

        self._unique_dates = sorted(self._all_data_df["date"].unique().tolist())
        logging.info(f"Loaded data for {len(self.symbols)} symbols across {len(self._unique_dates)} unique trading days.")