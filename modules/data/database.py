import logging
import psycopg2
from psycopg2.extensions import connection as PgConnection

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Database:
    """
    Responsible for handling the database connection and schema management (TimescaleDB)
    """
    def __init__(self):
        self.conn = None

    def get_connection(self) -> PgConnection:
        if self.conn and not self.conn.closed:
            return self.conn
        
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.conn.autocommit = False
            logging.info("Successfully connected to the database")
            return self.conn
        except psycopg2.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def close_connection(self):
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")
            self.conn = None

    