
from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, insert, select
from src.data.database import Database
from src.data.eod_prices.model import EODPrice


class EODPriceRepository:
    def __init__(self):
        self.db_session_context= Database.get_db_session

    def save_eod_prices(self, prices_data: List[Dict[str, Any]]) -> None:
        if not prices_data:
            logging.warning("No EOD prices provided to save.")
            return
        
        with self.db_session_context() as session:
            try:
                stmt = insert(EODPrice).values(prices_data)
                session.execute(stmt)
                session.commit()
                logging.info(f"Successfully saved {len(prices_data)} EOD prices.")
            except Exception as e:
                session.rollback()
                logging.error(f"Error saving EOD prices: {e}")
                raise

    def get_eod_prices_by_symbol(
            self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None 
    ) -> List[EODPrice]:
        with self.db_session_context() as session:
            stmt = select(EODPrice).where(EODPrice.symbol == symbol)

            if start_date:
                stmt = stmt.where(EODPrice.time >= start_date)
            if end_date:
                stmt = stmt.where(EODPrice.time <= end_date)

            stmt = stmt.order_by(EODPrice.time)

            result = session.execute(stmt).scalars().all()
            logging.info(f"Retrieved {len(result)} EOD prices for symbol '{symbol}'.")
            return result
            
    
    def get_latest_eod_price_date(self, symbol: str) -> Optional[datetime]:
        with self.db_session_context() as session:
            stmt = select(EODPrice.time) \
                .where(EODPrice.symbol == symbol) \
                .order_by(EODPrice.time.desc()) \
                .limit(1)

            result = session.execute(stmt).scalar_one_or_none()
            return result

    def count_eod_prices_by_symbol(self, symbol: str) -> int:
        with self.db_session_context() as session:
            stmt = select(func.count(EODPrice.time)).where(EODPrice.symbol == symbol)
            count = session.execute(stmt).scalar_one()
            return count

    def delete_eod_prices_by_symbol(self, symbol: str) -> None:
        with self.db_session_context() as session:
            try:
                stmt = delete(EODPrice).where(EODPrice.symbol == symbol)
                result = session.execute(stmt)
                session.commit()
                logging.info(f"Deleted {result.rowcount} EOD prices for symbol '{symbol}'.")
            except Exception as e:
                session.rollback()
                logging.error(f"Error deleting EOD prices for '{symbol}': {e}")
                raise