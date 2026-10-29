import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(String(100))
    url = Column(String(500), unique=True)
    published_at = Column(DateTime, index=True)
    ticker = Column(String(20), index=True)
    sentiment_score = Column(Float, default=0.0)  # actually the source credibility score
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "url": self.url,
            "published_at": str(self.published_at) if self.published_at else None,
            "ticker": self.ticker,
            "sentiment_score": self.sentiment_score,
        }


class EtlRun(Base):
    """One row per ETL run, used for monitoring and for the numbers in the README."""

    __tablename__ = "etl_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    raw_items = Column(Integer, default=0)            # items returned by the API
    batch_duplicates = Column(Integer, default=0)     # repeated URLs inside this run
    invalid = Column(Integer, default=0)              # missing title or URL
    existing_duplicates = Column(Integer, default=0)  # URL already in the database
    inserted = Column(Integer, default=0)             # new rows
    fetch_errors = Column(Integer, default=0)
    seconds = Column(Float)


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment or .env file")

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create tables that do not exist yet (existing tables are left untouched)."""
    Base.metadata.create_all(engine)
    print("Database tables ready")


def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("Connected to PostgreSQL")
        return True
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return False
