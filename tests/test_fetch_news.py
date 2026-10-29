from etl.fetch_news import (
    extract_ticker, extract_tickers, normalize_article, normalize_url, parse_published_at,
)


# --- URL normalisation ------------------------------------------------------
def test_tracking_parameters_removed():
    assert normalize_url("https://Example.com/a?utm_source=x&id=7&fbclid=abc") == "https://example.com/a?id=7"


def test_trailing_slash_and_fragment_removed():
    assert normalize_url("https://example.com/a/#top") == normalize_url("https://example.com/a")


def test_empty_url():
    assert normalize_url("") == ""
    assert normalize_url("   ") == ""


# --- ticker extraction ------------------------------------------------------
def test_ticker_symbols_found_in_order():
    assert extract_tickers("ETH jumps while BTC slips") == ["ETH", "BTC"]


def test_cashtag_and_names():
    assert extract_tickers("$SOL rallies as Bitcoin holds") == ["SOL", "BTC"]


def test_common_words_are_not_tickers():
    # These were false positives when the text was upper-cased before matching.
    assert extract_tickers("Click the link, add a dot, visit the uni and ask ada") == []


def test_no_partial_matches():
    assert extract_tickers("BTCUSD and ETHEREUMX are not tickers") == []


def test_duplicates_collapsed():
    assert extract_tickers("BTC BTC Bitcoin") == ["BTC"]


def test_primary_ticker_prefers_title_then_description_then_category():
    assert extract_ticker({"title": "SOL surges", "description": "BTC flat"}) == "SOL"
    assert extract_ticker({"title": "Markets quiet", "description": "ETH flat"}) == "ETH"
    assert extract_ticker({"title": "Quiet", "category": "bitcoin"}) == "BTC"
    assert extract_ticker({"title": "Quiet", "category": "macro"}) == "MACRO"
    assert extract_ticker({"title": "Quiet"}) == "CRYPTO"


# --- normalisation ----------------------------------------------------------
def test_parse_published_at():
    assert parse_published_at("2026-10-01T12:30:00Z").year == 2026
    assert parse_published_at("not a date") is None
    assert parse_published_at(None) is None


def test_normalize_article_uses_link_or_url_and_trims():
    a = normalize_article({"title": "  Hello  ", "link": "https://x.com/p/?utm_medium=a", "credibility": "0.8"})
    assert a["title"] == "Hello"
    assert a["url"] == "https://x.com/p"
    assert a["sentiment_score"] == 0.8
