from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.config import settings

Base = declarative_base()

class Ranking(Base):
    """Model for storing restaurant rankings"""
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True)
    restaurant_slug = Column(String, nullable=False)
    rank = Column(Integer, nullable=False)
    rating = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

async def init_db():
    """Initialize database and create tables"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine) 