"""Latency benchmark: retrieval alone, and the full ask() call including the LLM.

Usage: python -m scripts.benchmark [eval/questions.json] [repeats]
The first call loads the embedding model, so it is run once as a warm-up and excluded.
"""
import json
import statistics
import sys
import time

from rag.index import search
from rag.qa import ask


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(p / 100 * (len(ordered) - 1)))]


def timed(fn, *args) -> float:
    t0 = time.perf_counter()
    fn(*args)
    return time.perf_counter() - t0


def main(path: str = "eval/questions.json", repeats: int = 1) -> None:
    questions = [q["question"] for q in json.load(open(path))] * repeats
    search("warm up")  # model load + index load
    retrieval = [timed(search, q) for q in questions]
    full = [timed(ask, q) for q in questions]
    for name, vals in (("retrieval", retrieval), ("end-to-end ask()", full)):
        print(f"{name:18s} n={len(vals)}  median={statistics.median(vals) * 1000:.0f} ms  "
              f"p95={pct(vals, 95) * 1000:.0f} ms")
    print(f"approx. LLM share of end-to-end: {1 - statistics.median(retrieval) / statistics.median(full):.0%}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "eval/questions.json",
         int(sys.argv[2]) if len(sys.argv) > 2 else 1)
