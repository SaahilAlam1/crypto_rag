import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

NEWS_API_URL = "https://cryptocurrency.cv/api/news"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CryptoNewsRAG/1.0)"}

CATEGORIES = [
    "general", "bitcoin", "ethereum", "defi", "solana",
    "stablecoin", "nft", "layer2", "macro", "security",
]

# Fallback labels when no ticker is found in the text. These are topic labels,
# not real tickers, so they are only used as a last resort.
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

NAME_TO_TICKER = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL", "ripple": "XRP",
    "cardano": "ADA", "dogecoin": "DOGE", "tether": "USDT", "binance coin": "BNB",
    "avalanche": "AVAX", "polkadot": "DOT", "polygon": "MATIC",
    "chainlink": "LINK", "uniswap": "UNI",
}

# Case-sensitive on purpose: "LINK" the token, not "link" the word.
_TICKER_RE = re.compile(r"(?<![A-Za-z0-9])\$?(" + "|".join(KNOWN_TICKERS) + r")(?![A-Za-z0-9])")
_NAME_RE = re.compile(r"\b(" + "|".join(NAME_TO_TICKER) + r")\b", re.IGNORECASE)

_TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src"}


def normalize_url(url: str) -> str:
    """Lower-case host, drop fragments, tracking parameters and trailing slashes."""
    url = (url or "").strip()
    if not url:
        return ""
    parts = urlsplit(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def extract_tickers(text: str) -> list[str]:
    """Return tickers mentioned in text, in order of first appearance, without duplicates."""
    found: list[tuple[int, str]] = []
    for m in _TICKER_RE.finditer(text or ""):
        found.append((m.start(), m.group(1)))
    for m in _NAME_RE.finditer(text or ""):
        found.append((m.start(), NAME_TO_TICKER[m.group(1).lower()]))
    found.sort()
    seen: list[str] = []
    for _, ticker in found:
        if ticker not in seen:
            seen.append(ticker)
    return seen


def extract_ticker(article: dict[str, Any]) -> str:
    """Primary ticker: first one in the title, then the description, then the category label."""
    for field in ("title", "description"):
        tickers = extract_tickers(article.get(field) or "")
        if tickers:
            return tickers[0]
    category = (article.get("category") or "").lower()
    if category in CATEGORY_TICKER:
        return CATEGORY_TICKER[category]
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
        "url": normalize_url(raw.get("link") or raw.get("url") or ""),
        "published_at": parse_published_at(raw.get("pubDate") or raw.get("published_at")),
        "ticker": extract_ticker(raw),
        # The API field is a source-credibility score, not sentiment.
        "sentiment_score": float(raw.get("credibility") or 0.0),
    }


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(HEADERS)
    return session


_SESSION = _make_session()


def fetch_page(category: str | None = None, page: int = 1) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page}
    if category:
        params["category"] = category
    response = _SESSION.get(NEWS_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_articles_with_stats(
    categories: list[str] | None = None,
    max_pages_per_category: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Fetch, normalise and de-duplicate within the batch. Returns (articles, stats)."""
    categories = categories or CATEGORIES
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []
    stats = {"raw_items": 0, "no_url": 0, "batch_duplicates": 0, "fetch_errors": 0}

    for category in categories:
        for page in range(1, max_pages_per_category + 1):
            try:
                payload = fetch_page(category=category, page=page)
            except Exception:
                logger.exception("Error fetching %s page %s", category, page)
                stats["fetch_errors"] += 1
                break
            raw_articles = payload.get("articles") or []
            if not raw_articles:
                break
            for raw in raw_articles:
                stats["raw_items"] += 1
                normalized = normalize_article(raw)
                url = normalized["url"]
                if not url:
                    stats["no_url"] += 1
                    continue
                if url in seen_urls:
                    stats["batch_duplicates"] += 1
                    continue
                seen_urls.add(url)
                articles.append(normalized)
            if not (payload.get("pagination") or {}).get("hasMore", False):
                break

    logger.info("Fetched %s unique articles (%s raw)", len(articles), stats["raw_items"])
    return articles, stats


def fetch_articles(categories=None, max_pages_per_category: int = 5) -> list[dict[str, Any]]:
    """Backwards-compatible wrapper returning only the articles."""
    return fetch_articles_with_stats(categories, max_pages_per_category)[0]


def fetch_news(max_pages: int = 5) -> list[dict[str, Any]]:
    """Alias for fetch_articles."""
    return fetch_articles(max_pages_per_category=max_pages)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = fetch_articles(categories=["bitcoin"], max_pages_per_category=1)
    for article in sample[:3]:
        print(f"- [{article['ticker']}] {article['title'][:70]}")
        print(f"  {article['source']} | {article['published_at']}")
