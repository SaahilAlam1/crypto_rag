"""Print random articles so you can write evaluation questions about them.

Usage: python -m eval.sample_articles 40
Then write eval/questions.json (see eval/questions.example.json).
"""
import sys

from sqlalchemy import func

from etl.database import NewsArticle, SessionLocal


def main(n: int = 40) -> None:
    session = SessionLocal()
    try:
        rows = session.query(NewsArticle).order_by(func.random()).limit(n).all()
        for r in rows:
            print(f"{r.id} | {r.ticker} | {r.title}\n    {r.url}")
    finally:
        session.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
