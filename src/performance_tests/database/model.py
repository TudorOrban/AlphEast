
from sqlalchemy import Column, DateTime, Integer, Numeric, String
from performance_tests.database.base_model import Base


class PriceBarEntity(Base):
    """
    SQLAlchemy ORM model for storing price bar data across different intervals.
    This model serves as the database-specific representation that matches
    the properties of the library-agnostic PriceBar dataclass.
    """
    __tablename__ = "price_bars"

    time = Column(DateTime(timezone=False), primary_key=True, comment="Timestamp of the price bar")
    symbol = Column(String, primary_key=True, comment="Trading symbol of the asset")
    
    open = Column(Numeric(15, 6), nullable=False, comment="Opening price of the bar")
    high = Column(Numeric(15, 6), nullable=False, comment="Highest price of the bar")
    low = Column(Numeric(15, 6), nullable=False, comment="Lowest price of the bar")
    close = Column(Numeric(15, 6), nullable=False, comment="Closing price of the bar")
    volume = Column(Integer, nullable=False, comment="Volume traded during the bar")

    def __repr__(self):
        return (
            f"<PriceBarEntity(symbol='{self.symbol}', time='{self.time}', "
            f"close={self.close})>"
        )