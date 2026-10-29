"""Retrieval evaluation: for each question, is the expected article in the top-k results?

Usage: python -m eval.run_eval [eval/questions.json] [k]
Reports hit@1, hit@k and mean reciprocal rank (MRR), and lists the misses.
"""
import json
import sys

from rag.index import search


def main(path: str = "eval/questions.json", k: int = 5) -> None:
    items = json.load(open(path))
    hit1 = hitk = 0
    reciprocal = []
    misses = []
    for item in items:
        urls = [r["url"] for r in search(item["question"], top_k=k)]
        expected = item["expected_url"]
        if expected in urls:
            rank = urls.index(expected) + 1
            hit1 += rank == 1
            hitk += 1
            reciprocal.append(1 / rank)
        else:
            reciprocal.append(0.0)
            misses.append(item["question"])
    n = len(items)
    print(f"Questions: {n}")
    print(f"hit@1: {hit1 / n:.1%}")
    print(f"hit@{k}: {hitk / n:.1%}")
    print(f"MRR:   {sum(reciprocal) / n:.3f}")
    if misses:
        print("\nMisses:")
        for q in misses:
            print(f"- {q}")


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "eval/questions.json",
        int(sys.argv[2]) if len(sys.argv) > 2 else 5,
    )
