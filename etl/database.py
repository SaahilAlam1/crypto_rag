from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(String(100))
    url = Column(String(500), unique=True)
    published_at = Column(DateTime, index=True)
    ticker = Column(String(20), index=True)
    sentiment_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'source': self.source,
            'url': self.url,
            'published_at': str(self.published_at) if self.published_at else None,
            'ticker': self.ticker,
            'sentiment_score': self.sentiment_score
        }

# Create database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Successfully connected to PostgreSQL!")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running (brew services list)")
        print("2. Check your .env file has correct credentials")
        print("3. Verify database exists (psql -U crypto_user -d crypto_news_rag)")
        return False
