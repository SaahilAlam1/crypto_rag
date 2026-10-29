"""Streamlit UI for Crypto News ETL + RAG Insight Service."""

import streamlit as st

from analytics.queries import (
    article_count,
    articles_per_ticker_per_day,
    recent_headlines,
    top_sources,
)
from etl.pipeline import run_etl
from rag.index import build_index
from rag.qa import ask

st.set_page_config(page_title="Crypto News RAG", page_icon="📰", layout="wide")
st.title("Crypto News ETL + RAG Insight Service")
st.caption("Ingest crypto/finance news → PostgreSQL → FAISS retrieval → DeepSeek LLM answers")

tab_ask, tab_analytics, tab_etl = st.tabs(["Ask Questions", "Analytics", "ETL Pipeline"])

with tab_ask:
    st.subheader("Ask about ingested news")
    question = st.text_input(
        "Your question",
        placeholder='e.g. "Summarise recent BTC news" or "What risks are mentioned about stablecoins?"',
    )
    top_k = st.slider("Articles to retrieve", 3, 10, 5)
    if st.button("Ask", type="primary") and question:
        with st.spinner("Searchines and generating answer..."):
            result = ask(question, top_k=top_k)
        st.markdown("### Answer")
        st.write(result["answer"])
        if result["sources"]:
            st.markdown("### Sources")
            for src in result["sources"]:
                if src.get("url"):
                    st.markdown(f"- [{src['title']}]({src['url']}) — {src.get('source', '')}")
                else:
                    st.markdown(f"- {src['title']} — {src.get('source', '')}")

with tab_analytics:
    st.subheader("Analytics")
    count = article_count()
    st.metric("Total articles in DB", count)

    if count == 0:
        st.info("No articles yet. Run the ETL pipeline in the **ETL Pipeline** tab.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Articles per ticker (last 7 days)")
            df_daily = articles_per_ticker_per_day(days=7)
            if not df_daily.empty:
                st.dataframe(df_daily, width='stretch')
            else:
                st.write("No recent articles with dates.")

        with col2:
            st.markdown("#### Top sources")
            df_sources = top_sources(limit=10)
            st.dataframe(df_sources, width='stretch')

        st.markdown("#### Recent headlines by ticker")
        ticker = st.text_input("Ticker", value="BTC").upper()
        if ticker:
            df_headlines = recent_headlines(ticker, limit=10)
            if not df_headlines.empty:
                st.dataframe(
                    df_headlines[["title", "source", "published_at", "url"]],
                    width='stretch',
                )
            else:
                st.write(f"No headlines found for {ticker}.")

with tab_etl:
    st.subheader("Run ETL Pipeline")
    st.write(
        "Fetches news from [cryptocurrency.cv](https://cryptocurrency.cv/api/news) "
        "(no API key), normalizes fields, and loads into PostgreSQL."
    )
    pages = st.slider("Max pages per category", 1, 20, 5)
    if st.button("Run ETL", type="primary"):
        with st.spinner("Fetching and loading articles..."):
            result = run_etl(max_pages_per_category=pages)
        st.success(
            f"Fetched **{result['fetched']}** articles — "
            f"inserted **{result['inserted']}**, skipped **{result['skipped']}** (duplicates)"
        )

    st.divider()
    st.subheader("Rebuild vector index")
    st.write("Re-embed all DB articles into FAISS after loading new data.")
    if st.button("Rebuild FAISS index"):
        with st.spinner("Building embeddings..."):
            index_result = build_index(force=True)
        if index_result.get("status") == "empty":
            st.warning("No articles in DB to index.")
        else:
            st.success(f"Indexed **{index_result.get('count', 0)}** articles.")
