"""Fetch crypto/finance news from cryptocurrency.cv (no API key required)."""

import re
from datetime import datetime
from typing import Any

import requests

NEWS_API_URL = "https://cryptocurrency.cv/api/news"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CryptoNewsRAG/1.0)"}

CATEGORIES = [
    "general", "bitcoin", "ethereum", "defi", "solana",
    "stablecoin", "nft", "layer2", "macro", "security",
]

CATEGORY_TICKER = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "defi": "DEFI",
    "stablecoin": "STABLE",
    "nft": "NFT",
    "layer2": "L2",
}

KNOWN_TICKERS = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "USDT", "USDC",
    "BNB", "AVAX", "DOT", "MATIC", "LINK", "UNI", "AAVE",
]


def extract_ticker(article: dict[str, Any]) -> str:
    category = (article.get("category") or "").lower()
    if category in CATEGORY_TICKER:
        return CATEGORY_TICKER[category]

    text = f"{article.get('title', '')} {article.get('description', '')}".upper()
    for ticker in KNOWN_TICKERS:
        if re.search(rf"\b{ticker}\b", text):
            return ticker
    return category.upper() if category else "CRYPTO"


def parse_published_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def normalize_article(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": (raw.get("title") or "").strip(),
        "description": (raw.get("description") or "").strip() or None,
        "source": (raw.get("source") or "Unknown").strip(),
        "url": (raw.get("link") or raw.get("url") or "").strip(),
        "published_at": parse_published_at(raw.get("pubDate") or raw.get("published_at")),
        "ticker": extract_ticker(raw),
        "sentiment_score": float(raw.get("credibility") or 0.0),
    }


def fetch_page(category: str | None = None, page: int = 1) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page}
    if category:
        params["category"] = category
    response = requests.get(NEWS_API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_articles(
    categories: list[str] | None = None,
    max_pages_per_category: int = 5,
) -> list[dict[str, Any]]:
    """Fetch and dedupe articles across categories and pages."""
    categories = categories or CATEGORIES
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []

    for category in categories:
        for page in range(1, max_pages_per_category + 1):
            try:
                payload = fetch_page(category=category, page=page)
                raw_articles = payload.get("articles") or []
                if not raw_articles:
                    break

                for raw in raw_articles:
                    normalized = normalize_article(raw)
                    url = normalized["url"]
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    articles.append(normalized)

                pagination = payload.get("pagination") or {}
                if not pagination.get("hasMore", False):
                    break
            except Exception as e:
                print(f"Error fetching {category} page {page}: {e}")
                break

    print(f"✅ Fetched {len(articles)} articles")
    return articles


# Alias for backwards compatibility
def fetch_news(max_pages: int = 5) -> list[dict[str, Any]]:
    """Alias for fetch_articles."""
    return fetch_articles(max_pages_per_category=max_pages)


if __name__ == "__main__":
    sample = fetch_articles(categories=["bitcoin"], max_pages_per_category=1)
    print(f"Fetched {len(sample)} articles")
    for article in sample[:3]:
        print(f"- [{article['ticker']}] {article['title'][:70]}")
        print(f"  {article['source']} | {article['published_at']}")
