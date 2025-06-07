from datetime import datetime
from decimal import Decimal
import logging
import sys

from sqlalchemy import text
from src.data.eod_prices.repository import EODPriceRepository
from src.data.database import Database


logging.info("Starting database connection test...")
try:
    Database.initialize()

    with Database.get_db_session() as session:
        result = session.execute(text("SELECT version();")).scalar()
        logging.info(f"Successfully retrieved database version: {result}")

    logging.info("Database connection test PASSED.")

except Exception as e:
    logging.error(f"Database connection test FAILED: {e}")
    sys.exit(1) 

repo = EODPriceRepository()

# --- Test 2b: Get EOD Prices by Symbol ---
logging.info("\n--- Test 2b: Getting EOD Prices for AAPL ---")
try:
    aapl_prices = repo.get_eod_prices_by_symbol("AAPL")
    for price in aapl_prices:
        logging.info(f"Retrieved: {price}")
    assert len(aapl_prices) == 2, "Expected 2 AAPL prices"
    logging.info("AAPL prices retrieval test PASSED.")
except Exception as e:
    logging.error(f"Error during get_eod_prices_by_symbol test (AAPL): {e}")
