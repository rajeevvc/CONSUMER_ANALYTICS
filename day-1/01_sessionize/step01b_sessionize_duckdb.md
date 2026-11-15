# Learner guide — DuckDB SQL sessionization (`step01b_sessionize_duckdb_sql.py`)

## Goal

Same **30-minute inactivity** sessionization as pandas `step01_sessionize.py`, but implemented in **SQL over Parquet** with DuckDB. Optional parallel path for SQL learners.

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01b_sessionize_duckdb_sql.py
```

Requires: `duckdb`, and `day-1/data/web_events.parquet` (or generate parquet from CSV).

## Input / Output

| File | Role |
|------|------|
| `day-1/data/web_events.parquet` | Input (built from CSV if missing) |
| `day-1/output/sessionized_events_sql.parquet` | Event + session ids |
| `day-1/output/sessions_sql.parquet` | Session summaries |

## Note

Downstream Day‑1 scripts expect the **CSV** outputs from `step01_sessionize.py`. Use this file to practice SQL sessionization.

---

## Deep code walkthrough

### Paths

Same pattern as step01: `DAY1 = parents[1]`, then `DATA` / `OUTPUT`. Constants `SESSION_GAP_SECONDS=1800` and `DUPLICATE_GAP_SECONDS=2` match pandas.

### `ensure_web_events_parquet(con)`

1. If `web_events.parquet` exists → use it.  
2. Else if CSV exists → `COPY (SELECT * FROM read_csv_auto(...)) TO parquet`.  
3. Else raise.

This keeps SQL learners on columnar Parquet without requiring a separate ETL step.

### `SESSIONIZE_SQL` — CTE pipeline

Read the SQL top-to-bottom as stages:

| CTE | What it does |
|-----|----------------|
| `raw` | Read parquet; cast timestamp; drop null cookie/time/event |
| `ordered` | `lag()` over cookie×time for previous event/content |
| `deduped` | Drop rows where same event+content and gap ≤ 2s |
| `with_gap` | Recompute `gap_seconds` to previous **kept** event |
| `flagged` | `new_session = 1` if first event or `gap_seconds > 1800` |

Final `SELECT`:

```sql
session_idx = SUM(new_session) OVER (ORDER BY cookie, time ...)
session_id  = 'S' || lpad(session_idx, 9, '0')
```

That running sum is the SQL equivalent of pandas `cumsum(new_session)`.

**Window detail:** partitions are by `anonymous_id`; order is `timestamp, event_name` for deterministic ties.

### `SESSIONS_SQL`

Aggregates the temp table `sessionized_events`:

- `MIN`/`MAX` timestamp → session span  
- `arg_min(device_type, timestamp)` → device at first event  
- counts of events / distinct content  

This is a thinner summary than pandas (no furthest stage / conversion label). Teaching focus is the SQL session cut.

### `main()`

```text
connect DuckDB
  → ensure parquet
  → CREATE TEMP TABLE sessionized_events AS <SESSIONIZE_SQL>
  → CREATE TEMP TABLE sessions AS <SESSIONS_SQL>
  → COPY both to output parquet
  → print counts + the SQL text
```

Parameters bound into SQL: `[parquet_path, DUPLICATE_GAP_SECONDS, SESSION_GAP_SECONDS]` for the `?` placeholders.

---

## Teaching takeaway

Same rule as pandas sessionize, expressed as window functions. Proof that “30-minute idle” is a data definition, not a library trick.
