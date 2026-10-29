import json
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from etl.database import NewsArticle, SessionLocal

INDEX_DIR = Path("data/faiss_index")
MODEL_NAME = "all-MiniLM-L6-v2"

_cache: dict = {"mtime": None, "index": None, "docs": None}


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load the embedding model once per process (it was reloaded on every query before)."""
    return SentenceTransformer(MODEL_NAME)


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

    embeddings = get_model().encode([d["text"] for d in docs], show_progress_bar=False, convert_to_numpy=True)
    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(docs))
    _cache["mtime"] = None  # force reload on next search
    return {"status": "built", "count": len(docs), "path": str(INDEX_DIR)}


def _load_index():
    """Read the index from disk only when the file has changed."""
    index_path = INDEX_DIR / "index.faiss"
    meta_path = INDEX_DIR / "metadata.json"
    if not index_path.exists() or not meta_path.exists():
        build_index(force=True)
        if not index_path.exists():
            return None, None
    mtime = index_path.stat().st_mtime
    if _cache["mtime"] != mtime:
        _cache["index"] = faiss.read_index(str(index_path))
        _cache["docs"] = json.loads(meta_path.read_text())
        _cache["mtime"] = mtime
    return _cache["index"], _cache["docs"]


def search(query: str, top_k: int = 5) -> list[dict]:
    """Return top-k similar articles for a query."""
    index, docs = _load_index()
    if index is None or not docs:
        return []

    query_vec = get_model().encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, min(top_k, len(docs)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        results.append({**docs[idx], "score": float(score)})
    return results
