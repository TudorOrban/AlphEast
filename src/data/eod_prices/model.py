from sqlalchemy import Column, Integer, String, DateTime, Numeric
from src.data.base_model import Base

class EODPrice(Base):
    __tablename__ = 'eod_prices'

    time = Column(DateTime(timezone=False), primary_key=True)
    symbol = Column(String, primary_key=True)
    open = Column(Numeric(15, 6))
    high = Column(Numeric(15, 6))
    low = Column(Numeric(15, 6))
    close = Column(Numeric(15, 6))
    volume = Column(Integer)

    def __repr__(self):
        return f"<EODPrice(symbol='{self.symbol}', time='{self.time}', close={self.close})>"