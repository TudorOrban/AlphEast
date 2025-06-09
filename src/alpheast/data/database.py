import contextlib
import logging
from typing import Generator
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session

from alpheast.data.base_model import Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "alpheast_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cjql195jsov")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "example-key")

class Database:
    """
    Responsible for handling the database connection and schema management (TimescaleDB)
    """

    _engine: Engine = None
    _SessionLocal: sessionmaker = None
    
    @classmethod
    def initialize(cls):
        if cls._engine is None:
            db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            cls._engine = create_engine(db_url, pool_pre_ping=True)
            cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
            logging.info("SQLAlchemy Engine and SessionLocal initialized.")

    @classmethod
    def get_engine(cls) -> Engine:
        if cls._engine is None:
            cls.initialize()
        return cls._engine
    
    @classmethod
    @contextlib.contextmanager
    def get_db_session(cls) -> Generator[Session, None, None]:
        if cls._SessionLocal is None:
            cls.initialize()

        session: Session = cls._SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @classmethod
    def create_tables(cls):
        if cls._engine is None:
            cls.initialize()
        logging.info("Attempting to create all tables...")
        Base.metadata.create_all(bind=cls._engine)
        logging.info("All tables created or already exist.")

    @classmethod
    def drop_tables(cls):
        if cls._engine is None:
            cls.initialize()
        logging.warning("ATTENTION: Attempting to drop ALL tables. Data will be lost!")
        Base.metadata.drop_all(bind=cls._engine)
        logging.info("All tables dropped.")


Database.initialize()