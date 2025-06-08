
from datetime import date
import logging
from typing import List
from src.data.eod_prices.model import EODPrice
from src.data.eod_prices.repository import EODPriceRepository
from src.backtesting_engines.event_driven_engine.models.event import MarketEvent
from src.backtesting_engines.event_driven_engine.event_queue import EventQueue
from src.backtesting_engines.event_driven_engine.handlers.data_handler import DataHandler


class EODDatabaseDataHandler(DataHandler):
    """
    A concrete data handler that fetches End-Of-Day (EOD) price data
    from the database via EODPriceRepository
    """
    def __init__(self, event_queue: EventQueue, symbol: str, start_date: date, end_date: date):
        self.event_queue = event_queue
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.repository = EODPriceRepository()
        self._all_eod_prices: List[EODPrice] = []
        self._current_index = 0

        logging.info(f"EODDatabaseDataHandler initialized for {symbol} from {start_date} to {end_date}")
        self._load_data()

    def stream_next_market_event(self):
        """
        Retrieves the next EODPrice bar, creates a MarketEvent and puts it onto the queue
        """
        if not self.continue_backtest():
            logging.debug("No more EOD data to stream.")
            return
        
        eod_price = self._all_eod_prices[self._current_index]

        market_data = {
            "open": eod_price.open,
            "high": eod_price.high,
            "low": eod_price.low,
            "close": eod_price.close,
            "volume": eod_price.volume
        }

        market_event = MarketEvent(
            symbol=eod_price.symbol,
            timestamp=eod_price.time,
            data=market_data
        )
        self.event_queue.put(market_event)
        self._current_index += 1
        logging.debug(f"Pushed MarketEvent for {eod_price.symbol} on {eod_price.time.date()}")

    def continue_backtest(self) -> bool:
        return self._current_index < len(self._all_eod_prices)

    def _load_data(self):
        self._all_eod_prices = self.repository.get_eod_prices_by_symbol(
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self._all_eod_prices.sort(key=lambda x: x.time)

        if not self._all_eod_prices:
            logging.warning(f"No EOD prices found for {self.symbol} in range {self.start_date} - {self.end_date}. Backtest might not run.")