import logging
import sys

from sqlalchemy import text
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