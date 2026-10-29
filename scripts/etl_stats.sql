-- Overall numbers for the README and CV (run in psql or DBeaver)
SELECT count(*)                                             AS runs,
       round(avg(raw_items))                                AS avg_items_per_run,
       round(avg(inserted), 1)                              AS avg_new_per_run,
       round(100.0 * (sum(batch_duplicates) + sum(existing_duplicates))
             / NULLIF(sum(raw_items), 0), 1)                AS duplicate_pct,
       round(avg(seconds)::numeric, 1)                      AS avg_seconds,
       sum(fetch_errors)                                    AS fetch_errors
FROM etl_runs;

-- Articles by primary ticker
SELECT ticker, count(*) FROM news_articles GROUP BY ticker ORDER BY count(*) DESC LIMIT 15;
