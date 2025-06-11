
from datetime import date, datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, insert, select
from alpheast.models.price_bar import PriceBar
from alpheast.models.interval import Interval
from performance_tests.database.database import Database
from performance_tests.database.model import PriceBarEntity


class PriceDataRepository:
    """
    Repository for interacting with historical price data in the database.
    """
    def __init__(self):
        self.db_session_context = Database.get_db_session
        logging.info("PriceDataRepository initialized.")
        

    def save_price_bars(self, price_bars_data: List[Dict[str, Any]]) -> None:
        """
        Saves a list of price bar data dictionaries to the database.
        Assumes price_bars_data contains dictionaries matching PriceBarEntity columns.
        """
        if not price_bars_data:
            logging.warning("No price bars provided to save.")
            return
        
        with self.db_session_context() as session:
            try:
                stmt = insert(PriceBarEntity).values(price_bars_data)
                session.execute(stmt)
                session.commit()
                logging.info(f"Successfully saved {len(price_bars_data)} price bars.")
            except Exception as e:
                session.rollback()
                logging.error(f"Error saving price bars: {e}")
                raise

    def get_multiple_symbols_data(
        self,
        symbols: List[str],
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        interval: Interval = Interval.DAILY
    ) -> Dict[str, List[PriceBar]]:
        price_data: Dict[str, List[PriceBar]] = {}
        for symbol in symbols:
            price_bars: List[PriceBar] = self.get_price_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            price_data[symbol] = price_bars
        return price_data

    def get_price_data(
        self, 
        symbol: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        interval: Interval = Interval.DAILY
    ) -> List[PriceBar]:
        """
        Retrieves price data for a given symbol, date range, and interval.
        Converts fetched PriceBarEntity objects into PriceBar dataclass instances.
        """
        with self.db_session_context() as session:
            stmt = select(PriceBarEntity).where(PriceBarEntity.symbol == symbol)

            if start_date:
                stmt = stmt.where(PriceBarEntity.time >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                stmt = stmt.where(PriceBarEntity.time <= datetime.combine(end_date, datetime.max.time()))

            stmt = stmt.order_by(PriceBarEntity.time)

            result_entities: List[PriceBarEntity] = session.execute(stmt).scalars().all()
            logging.info(f"Retrieved {len(result_entities)} price bars for symbol '{symbol}' at interval '{interval.value}'.")
            
            price_bars = [
                PriceBar(
                    symbol=entity.symbol,
                    timestamp=entity.time,
                    open=entity.open,
                    high=entity.high,
                    low=entity.low,
                    close=entity.close,
                    volume=Decimal(entity.volume)
                ) for entity in result_entities
            ]
            return price_bars

    def get_latest_price_date(self, symbol: str) -> Optional[datetime]:
        """Retrieves the latest timestamp for a given symbol."""
        with self.db_session_context() as session:
            stmt = select(PriceBarEntity.time) \
                .where(PriceBarEntity.symbol == symbol) \
                .order_by(PriceBarEntity.time.desc()) \
                .limit(1)

            result = session.execute(stmt).scalar_one_or_none()
            return result

    def count_price_data_by_symbol(self, symbol: str) -> int:
        """Counts the number of price bars for a given symbol."""
        with self.db_session_context() as session:
            stmt = select(func.count(PriceBarEntity.time)).where(PriceBarEntity.symbol == symbol)
            count = session.execute(stmt).scalar_one()
            return count

    def delete_price_data_by_symbol(self, symbol: str) -> None:
        """Deletes all price bars for a given symbol."""
        with self.db_session_context() as session:
            try:
                stmt = delete(PriceBarEntity).where(PriceBarEntity.symbol == symbol)
                result = session.execute(stmt)
                session.commit()
                logging.info(f"Deleted {result.rowcount} price bars for symbol '{symbol}'.")
            except Exception as e:
                session.rollback()
                logging.error(f"Error deleting price bars for '{symbol}': {e}")
                raise