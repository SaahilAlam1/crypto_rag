"""Simple analytics queries over ingested news articles."""

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import func

from etl.database import NewsArticle, SessionLocal


def articles_per_ticker_per_day(days: int = 7) -> pd.DataFrame:
    since = datetime.utcnow() - timedelta(days=days)
    session = SessionLocal()
    try:
        rows = (
            session.query(
                func.date(NewsArticle.published_at).label("date"),
                NewsArticle.ticker,
                func.count(NewsArticle.id).label("count"),
            )
            .filter(NewsArticle.published_at >= since)
            .group_by(func.date(NewsArticle.published_at), NewsArticle.ticker)
            .order_by(func.date(NewsArticle.published_at).desc())
            .all()
        )
        return pd.DataFrame(rows, columns=["date", "ticker", "count"])
    finally:
        session.close()


def top_sources(limit: int = 10) -> pd.DataFrame:
    session = SessionLocal()
    try:
        rows = (
            session.query(
                NewsArticle.source,
                func.count(NewsArticle.id).label("count"),
            )
            .group_by(NewsArticle.source)
            .order_by(func.count(NewsArticle.id).desc())
            .limit(limit)
            .all()
        )
        return pd.DataFrame(rows, columns=["source", "count"])
    finally:
        session.close()


def recent_headlines(ticker: str, limit: int = 10) -> pd.DataFrame:
    session = SessionLocal()
    try:
        rows = (
            session.query(NewsArticle)
            .filter(NewsArticle.ticker == ticker.upper())
            .order_by(NewsArticle.published_at.desc().nullslast())
            .limit(limit)
            .all()
        )
        return pd.DataFrame([a.to_dict() for a in rows])
    finally:
        session.close()


def article_count() -> int:
    session = SessionLocal()
    try:
        return session.query(func.count(NewsArticle.id)).scalar() or 0
    finally:
        session.close()
