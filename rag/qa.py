"""RAG question-answering over ingested crypto news with DeepSeek."""

import os
import requests

from rag.index import search
from rag.market_data import get_market_summary

SYSTEM_PROMPT = """You are a crypto news analyst. Answer questions using ONLY the provided article snippets and market data.
If the context is insufficient, say so clearly. Cite sources by title when relevant.
Keep answers concise and factual."""


def _build_context(snippets: list[dict]) -> str:
    blocks = []
    for i, s in enumerate(snippets, 1):
        blocks.append(
            f"[{i}] {s['title']}\n"
            f"Source: {s.get('source', 'Unknown')} | Ticker: {s.get('ticker', 'N/A')}\n"
            f"{s['text'][:500]}"
        )
    return "\n\n".join(blocks)


def _call_deepseek(question: str, context: str, api_key: str) -> str:
    """Call DeepSeek API for answer generation."""
    api_url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'] or ""
        else:
            print(f"DeepSeek API error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"DeepSeek call failed: {e}")
        return ""


def ask(question: str, top_k: int = 5) -> dict:
    """Retrieve relevant articles and generate an answer via DeepSeek."""
    snippets = search(question, top_k=top_k)
    if not snippets:
        return {
            "answer": "No articles in the database yet. Run the ETL pipeline first.",
            "sources": [],
        }

    context = _build_context(snippets)
    
    # Add market data for price/ranking questions
    market_keywords = ["top", "price", "market cap", "ranking", "best", "largest"]
    if any(word in question.lower() for word in market_keywords):
        market_summary = get_market_summary()
        if market_summary:
            context = market_summary + "\n\n" + context
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key or api_key == "your_key_here":
        # Fallback: return retrieval-only results without LLM
        summary = f"Found {len(snippets)} relevant articles (DeepSeek key not configured):\n\n"
        summary += "\n".join(f"- {s['title']} ({s.get('source', '?')})" for s in snippets)
        return {
            "answer": summary,
            "sources": [{"title": s["title"], "url": s.get("url"), "source": s.get("source")} for s in snippets],
        }

    answer = _call_deepseek(question, context, api_key)
    
    if not answer:
        summary = f"Found {len(snippets)} relevant articles:\n\n"
        summary += "\n".join(f"- {s['title']} ({s.get('source', '?')})" for s in snippets)
        return {
            "answer": summary,
            "sources": [{"title": s["title"], "url": s.get("url"), "source": s.get("source")} for s in snippets],
        }
    
    return {
        "answer": answer,
        "sources": [
            {"title": s["title"], "url": s.get("url"), "source": s.get("source")}
            for s in snippets
        ],
    }
