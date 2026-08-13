"""RAG question-answering over ingested crypto news."""

import os

from openai import OpenAI

from rag.index import search

SYSTEM_PROMPT = """You are a crypto news analyst. Answer questions using ONLY the provided article snippets.
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


def ask(question: str, top_k: int = 5) -> dict:
    """Retrieve relevant articles and generate an answer via OpenAI."""
    snippets = search(question, top_k=top_k)
    if not snippets:
        return {
            "answer": "No articles in the database yet. Run the ETL pipeline first.",
            "sources": [],
        }

    context = _build_context(snippets)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_key_here":
        # Fallback: return retrieval-only results without LLM
        summary = f"Found {len(snippets)} relevant articles (OpenAI key not configured):\n\n"
        summary += "\n".join(f"- {s['title']} ({s.get('source', '?')})" for s in snippets)
        return {
            "answer": summary,
            "sources": [{"title": s["title"], "url": s.get("url"), "source": s.get("source")} for s in snippets],
        }

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.3,
        max_tokens=600,
    )
    answer = response.choices[0].message.content or ""
    return {
        "answer": answer,
        "sources": [
            {"title": s["title"], "url": s.get("url"), "source": s.get("source")}
            for s in snippets
        ],
    }
