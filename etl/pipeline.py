"""ETL pipeline: fetch news from API and load into PostgreSQL."""

from sqlalchemy.exc import IntegrityError

from etl.database import NewsArticle, SessionLocal, init_db
from etl.fetch_news import fetch_articles


def load_articles(articles: list[dict]) -> tuple[int, int]:
    """Insert articles, skipping duplicates by URL. Returns (inserted, skipped)."""
    inserted = 0
    skipped = 0
    session = SessionLocal()
    try:
        for data in articles:
            if not data.get("url") or not data.get("title"):
                skipped += 1
                continue
            article = NewsArticle(
                title=data["title"],
                description=data.get("description"),
                source=data.get("source"),
                url=data["url"],
                published_at=data.get("published_at"),
                ticker=data.get("ticker", "CRYPTO"),
                sentiment_score=data.get("sentiment_score", 0.0),
            )
            session.add(article)
            try:
                session.commit()
                inserted += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
    finally:
        session.close()
    return inserted, skipped


def run_etl(max_pages_per_category: int = 5, categories: list[str] | None = None) -> dict:
    """Run full ETL: fetch → normalize → load."""
    init_db()
    articles = fetch_articles(
        categories=categories,
        max_pages_per_category=max_pages_per_category,
    )
    inserted, skipped = load_articles(articles)
    return {
        "fetched": len(articles),
        "inserted": inserted,
        "skipped": skipped,
    }


if __name__ == "__main__":
    result = run_etl(max_pages_per_category=3)
    print(f"ETL complete: {result}")
