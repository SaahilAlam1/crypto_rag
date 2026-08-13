"""Build and query a FAISS vector index over article texts."""

import json
import os
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from etl.database import NewsArticle, SessionLocal

INDEX_DIR = Path("data/faiss_index")
MODEL_NAME = "all-MiniLM-L6-v2"


def _article_text(article: NewsArticle) -> str:
    parts = [article.title or ""]
    if article.description:
        parts.append(article.description)
    if article.ticker:
        parts.append(f"Ticker: {article.ticker}")
    return " | ".join(parts)


def load_articles_from_db() -> list[dict]:
    session = SessionLocal()
    try:
        articles = session.query(NewsArticle).order_by(NewsArticle.id).all()
        return [
            {
                "id": a.id,
                "text": _article_text(a),
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "ticker": a.ticker,
            }
            for a in articles
        ]
    finally:
        session.close()


def build_index(force: bool = False) -> dict:
    """Embed all DB articles and save FAISS index + metadata."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = INDEX_DIR / "index.faiss"
    meta_path = INDEX_DIR / "metadata.json"

    if index_path.exists() and meta_path.exists() and not force:
        return {"status": "exists", "path": str(INDEX_DIR)}

    docs = load_articles_from_db()
    if not docs:
        return {"status": "empty", "count": 0}

    model = SentenceTransformer(MODEL_NAME)
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(docs))

    return {"status": "built", "count": len(docs), "path": str(INDEX_DIR)}


def search(query: str, top_k: int = 5) -> list[dict]:
    """Return top-k similar articles for a query."""
    index_path = INDEX_DIR / "index.faiss"
    meta_path = INDEX_DIR / "metadata.json"
    if not index_path.exists() or not meta_path.exists():
        build_index(force=True)
        if not index_path.exists():
            return []

    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(str(index_path))
    docs = json.loads(meta_path.read_text())

    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, min(top_k, len(docs)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        doc = docs[idx]
        results.append({**doc, "score": float(score)})
    return results
