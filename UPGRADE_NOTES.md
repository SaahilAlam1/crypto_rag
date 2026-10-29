# Crypto RAG upgrade: how to apply

Copy these files over your repo (same paths). Work on a branch: `git checkout -b upgrade-v1`.

| File | Status | What changed |
|---|---|---|
| etl/fetch_news.py | replaced | URL normalisation, case-sensitive ticker extraction (fixes "link", "dot", "uni" false positives), retry session, logging, run statistics |
| etl/database.py | replaced | new `etl_runs` table, SQLAlchemy 2.0 `declarative_base` import |
| etl/pipeline.py | replaced | one bulk insert with `ON CONFLICT DO NOTHING`, separate duplicate / invalid counts, every run logged to `etl_runs` |
| etl/scheduler.py | new | APScheduler hourly job, rebuilds the FAISS index when new rows arrive |
| rag/index.py | replaced | embedding model and index cached (the model was reloaded on every query) |
| tests/test_fetch_news.py | new | 11 tests for URL normalisation and ticker extraction |
| eval/*, scripts/* | new | retrieval evaluation (hit@1, hit@5, MRR), latency benchmark, SQL for README numbers |
| Dockerfile, docker-compose.yml, .dockerignore, .env.example | new | one-command run |
| .github/workflows/ci.yml | new | runs pytest on every push |
| requirements.txt | replaced | starting point only: delete anything your other files do not import, add what they need |

Not changed: rag/qa.py, rag/market_data.py, app.py, analytics/. Check that `app.py` does not break
on the new keys returned by `run_etl` (old keys `fetched`, `inserted`, `skipped` are still present).

## Run
1. `cp .env.example .env` and set a real password (use the same one in both places).
2. `docker compose up --build`
3. Open http://localhost:8501

## Measure (for README and CV)
- After a few hourly runs: run `scripts/etl_stats.sql` (duplicate %, articles per run, seconds per run).
- `python -m eval.sample_articles 40`, write 30 questions into `eval/questions.json`, then
  `python -m eval.run_eval` (hit@5) and `python -m scripts.benchmark` (latency).

## Known limits
- Existing rows keep their old, un-normalised URLs, so an old article can be re-inserted once under its normalised URL.
- `ticker` still holds one value per article. A `tickers` array or join table needs a migration (Alembic).
- The `sentiment_score` column actually stores the source credibility score. Rename it or stop calling it sentiment in the README.
