# Learner guide — DuckDB SQL sessionization (`step01b_sessionize_duckdb_sql.py`)

## Goal (in plain English)

Same idea as pandas step01: **cut a cookie’s timeline when idle > 30 minutes**.

Difference: the heavy lifting is **SQL over Parquet** in DuckDB — useful if you think in windows/`LAG` instead of pandas.

**Important:** Downstream Day‑1 scripts expect the **CSV** from `step01_sessionize.py`. This path is for practice / comparison.

## How to run

From the repo root (needs `duckdb`; uses `web_events.parquet`, or builds it once from CSV):

```bash
python day-1/01_sessionize/step01b_sessionize_duckdb_sql.py
```

That script:

1. Ensures `day-1/data/web_events.parquet` exists  
2. Runs the sessionize SQL → temp table `sessionized_events`  
3. Runs the sessions SQL → temp table `sessions`  
4. Writes parquet outputs under `day-1/output/`

### Query the output tables (Python)

After the script finishes, the durable tables are parquet files. Query them with DuckDB (or load into pandas):

```python
import duckdb

EVENTS = "day-1/output/sessionized_events_sql.parquet"
SESSIONS = "day-1/output/sessions_sql.parquet"

con = duckdb.connect()

# Row counts
print(con.execute(f"SELECT count(*) AS n_events FROM read_parquet('{EVENTS}')").fetchdf())
print(con.execute(f"SELECT count(*) AS n_sessions FROM read_parquet('{SESSIONS}')").fetchdf())
print(
    con.execute(
        f"SELECT count(DISTINCT anonymous_id) AS n_cookies FROM read_parquet('{SESSIONS}')"
    ).fetchdf()
)

# Peek at sessionized events
print(
    con.execute(
        f"""
        SELECT anonymous_id, timestamp, event_name, gap_seconds, session_id
        FROM read_parquet('{EVENTS}')
        ORDER BY anonymous_id, timestamp
        LIMIT 20
        """
    ).fetchdf()
)

# Peek at session summaries
print(
    con.execute(
        f"""
        SELECT session_id, anonymous_id, session_start, session_end, n_events, n_content
        FROM read_parquet('{SESSIONS}')
        ORDER BY session_start
        LIMIT 20
        """
    ).fetchdf()
)

# Example: sessions with the most events
print(
    con.execute(
        f"""
        SELECT session_id, anonymous_id, n_events, session_start, session_end
        FROM read_parquet('{SESSIONS}')
        ORDER BY n_events DESC
        LIMIT 10
        """
    ).fetchdf()
)

# Optional: pandas
events_df = con.execute(f"SELECT * FROM read_parquet('{EVENTS}')").fetchdf()
sessions_df = con.execute(f"SELECT * FROM read_parquet('{SESSIONS}')").fetchdf()
print(events_df.head())
print(sessions_df.head())

con.close()
```

Output columns to expect:

| File | Useful columns |
|------|----------------|
| `sessionized_events_sql.parquet` | `anonymous_id`, `timestamp`, `event_name`, `gap_seconds`, `session_idx`, `session_id` |
| `sessions_sql.parquet` | `session_id`, `anonymous_id`, `session_start`, `session_end`, `n_events`, `n_content` |

## Input / Output

| File | Role |
|------|------|
| `day-1/data/web_events.parquet` | Input (from CSV if missing) |
| `day-1/output/sessionized_events_sql.parquet` | Events + session ids |
| `day-1/output/sessions_sql.parquet` | Session summaries |

---

## Big picture (intuition)

SQL CTEs mirror the pandas steps:

```text
raw → ordered (LAG) → deduped → with_gap → flagged (new_session)
        → running SUM(new_session) = session_idx
        → GROUP BY session_idx for summaries
```

---

## High-level variables

| Name | What it is |
|------|------------|
| `DAY1` / `DATA` / `OUTPUT` | Same folder layout as step01 |
| `WEB_EVENTS_PARQUET` / `WEB_EVENTS_CSV` | Source paths |
| `SESSION_GAP_SECONDS` | 1800 — new visit threshold |
| `DUPLICATE_GAP_SECONDS` | 2 — near-duplicate window |
| `SESSIONIZE_SQL` | Full SQL string that builds sessionized events |
| `SESSIONS_SQL` | Aggregate one row per `session_idx` |
| `con` | Open DuckDB connection |
| `parquet_path` | Path actually queried |
| `events_out` / `sessions_out` | Parquet write targets |

SQL placeholders `?` are bound in order: parquet path, duplicate gap, session gap.

---

## Deep code walkthrough (every function + SQL stages)

### `ensure_web_events_parquet(con)`

**Job:** Make sure Parquet exists for DuckDB to read fast.

1. If parquet exists → return it.  
2. Else if CSV exists → `COPY (... read_csv_auto ...) TO parquet` with ZSTD.  
3. Else raise.

**Returns:** Path to parquet.

---

### `SESSIONIZE_SQL` (CTE chain)

| CTE | Plain meaning |
|-----|----------------|
| `raw` | Read parquet; keep non-null cookie/time/event |
| `ordered` | Per cookie, `LAG` previous time/event/content |
| `deduped` | Drop near-duplicates (same event+content within 2s) |
| `with_gap` | Gap seconds to previous **kept** event |
| `flagged` | `new_session = 1` if first event or gap > 30 min |
| final `SELECT` | Running `SUM(new_session)` → `session_idx` / `session_id` |

`session_id` is `'S' || lpad(session_idx, 9, '0')` — same style as pandas.

---

### `SESSIONS_SQL`

**Job:** Collapse events to visits.

Per `session_idx`: first/last timestamp, first device/referrer (`arg_min`), event count, distinct content.

(Does **not** attach the 7-day conversion label — that stays on the pandas teaching path.)

---

### `main()`

**Job:** Orchestrate DuckDB work.

```text
connect
parquet = ensure_web_events_parquet(con)
CREATE TEMP TABLE sessionized_events AS <SESSIONIZE_SQL>
CREATE TEMP TABLE sessions AS <SESSIONS_SQL>
COPY both tables to parquet outputs
print counts + print the SQL used
close connection
```

---

## Acceptance checks

- Event and session parquet files written  
- Cookie/session counts in the same ballpark as pandas step01 on the same data  
- Downstream labs still run from **CSV** step01 outputs  

## Teaching takeaway

Answer: *“Sessionization is a rule, not a library — SQL or pandas can express the same cut.”*
