import logging
import time
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from etl.database import EtlRun, NewsArticle, SessionLocal, init_db
from etl.fetch_news import fetch_articles_with_stats

logger = logging.getLogger(__name__)
CHUNK = 500


def _row(data: dict) -> dict:
    return {
        "title": data["title"],
        "description": data.get("description"),
        "source": data.get("source"),
        "url": data["url"],
        "published_at": data.get("published_at"),
        "ticker": data.get("ticker", "CRYPTO"),
        "sentiment_score": data.get("sentiment_score", 0.0),
    }


def load_articles(articles: list[dict]) -> dict[str, int]:
    """Insert in bulk, skipping URLs that already exist.

    Returns counts: inserted, existing_duplicates, invalid.
    """
    rows = [_row(a) for a in articles if a.get("url") and a.get("title")]
    invalid = len(articles) - len(rows)
    inserted = 0
    session = SessionLocal()
    try:
        for i in range(0, len(rows), CHUNK):
            chunk = rows[i:i + CHUNK]
            stmt = (
                insert(NewsArticle)
                .values(chunk)
                .on_conflict_do_nothing(index_elements=["url"])
                .returning(NewsArticle.id)
            )
            inserted += len(session.execute(stmt).fetchall())
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"inserted": inserted, "existing_duplicates": len(rows) - inserted, "invalid": invalid}


def run_etl(max_pages_per_category: int = 5, categories: list[str] | None = None) -> dict:
    """Run full ETL: fetch, normalise, load, and record the run."""
    init_db()
    started = datetime.utcnow()
    t0 = time.perf_counter()

    articles, fetch_stats = fetch_articles_with_stats(categories, max_pages_per_category)
    load_stats = load_articles(articles)
    seconds = round(time.perf_counter() - t0, 2)

    result = {
        "raw_items": fetch_stats["raw_items"],
        "batch_duplicates": fetch_stats["batch_duplicates"],
        "fetch_errors": fetch_stats["fetch_errors"],
        "invalid": load_stats["invalid"] + fetch_stats["no_url"],
        "existing_duplicates": load_stats["existing_duplicates"],
        "inserted": load_stats["inserted"],
        "seconds": seconds,
        # kept for the Streamlit UI, which expects these keys
        "fetched": len(articles),
        "skipped": load_stats["existing_duplicates"] + load_stats["invalid"],
    }

    session = SessionLocal()
    try:
        session.add(EtlRun(
            started_at=started,
            finished_at=datetime.utcnow(),
            raw_items=result["raw_items"],
            batch_duplicates=result["batch_duplicates"],
            invalid=result["invalid"],
            existing_duplicates=result["existing_duplicates"],
            inserted=result["inserted"],
            fetch_errors=result["fetch_errors"],
            seconds=seconds,
        ))
        session.commit()
    finally:
        session.close()
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(f"ETL complete: {run_etl(max_pages_per_category=3)}")
