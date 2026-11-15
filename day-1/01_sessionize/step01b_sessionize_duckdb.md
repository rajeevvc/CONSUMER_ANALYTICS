# Learner guide — DuckDB SQL sessionization (`step01b_sessionize_duckdb_sql.py`)

## Goal

Same **30-minute inactivity** sessionization as pandas `step01_sessionize.py`, but implemented in **SQL over Parquet** with DuckDB. Optional parallel path for SQL learners.

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01b_sessionize_duckdb_sql.py
```

Requires: `duckdb`, and `day-1/data/web_events.parquet` (or generate parquet from CSV).

## Input

| File | Used? |
|------|--------|
| `day-1/data/web_events.parquet` | **Yes** |

Same logical fields as CSV sessionize: cookie, timestamp, event, content, device, referrer.

## What you must implement (SQL)

1. Read parquet into a CTE  
2. Window by `anonymous_id` ordered by time  
3. Drop near-duplicates (same event/content, gap ≤ 2s)  
4. Flag `new_session` when first event or gap > 1800s  
5. `session_idx` = running sum of `new_session`  
6. Write event-level and session-level parquet outputs  

## Output

| File | Grain |
|------|--------|
| `day-1/output/sessionized_events_sql.parquet` | Event + session ids |
| `day-1/output/sessions_sql.parquet` | Session summaries |

## Note

Downstream Day‑1 scripts (`journey_analysis`, HMM, features, segmentation) expect the **CSV** outputs from `step01_sessionize.py`. Use this file to practice SQL sessionization; keep CSV path for the rest of the lab unless you adapt loaders.
