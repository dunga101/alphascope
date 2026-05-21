from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    sp500 = Column(Float)
    nasdaq100 = Column(Float)
    dow = Column(Float)
    russell2000 = Column(Float)
    vix = Column(Float)
    us10y = Column(Float)

    market_regime = Column(String(50))
    confidence_score = Column(Float)


class SymbolSnapshot(Base):
    __tablename__ = "symbol_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    symbol = Column(String(20), nullable=False, index=True)

    price = Column(Float)
    rsi = Column(Float)
    sma20 = Column(Float)
    sma50 = Column(Float)
    volume_ratio = Column(Float)

    signal = Column(String(50))
    confidence = Column(Float)


class NewsEvent(Base):
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    headline = Column(Text, nullable=False)
    source = Column(String(100))
    symbol = Column(String(20), index=True)

    event_type = Column(String(50))
    sentiment = Column(String(20))
    impact_score = Column(Float)


class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    quick_take = Column(Text)
    executive_summary = Column(Text)

    market_regime = Column(String(50))
    confidence = Column(Float)
