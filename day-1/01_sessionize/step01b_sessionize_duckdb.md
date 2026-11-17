# Learner guide — DuckDB SQL sessionization (`step01b_sessionize_duckdb_sql.py`)

## Goal (in plain English)

Same idea as pandas step01: **cut a cookie’s timeline when idle > 30 minutes**.

Difference: the heavy lifting is **SQL over Parquet** in DuckDB — useful if you think in windows/`LAG` instead of pandas.

**Important:** Downstream Day‑1 scripts expect the **CSV** from `step01_sessionize.py`. This path is for practice / comparison.

## How to run

### Option A — Python script (recommended)

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

After Option A finishes, the durable tables are parquet files. Query them with DuckDB (or load into pandas):

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

### Option B — Python that calls the same SQL

```python
import sys
import duckdb

sys.path.insert(0, "day-1/01_sessionize")
from step01b_sessionize_duckdb_sql import (
    SESSIONIZE_SQL,
    SESSIONS_SQL,
    ensure_web_events_parquet,
    DUPLICATE_GAP_SECONDS,
    SESSION_GAP_SECONDS,
    OUTPUT,
)

con = duckdb.connect()
parquet_path = ensure_web_events_parquet(con)
OUTPUT.mkdir(parents=True, exist_ok=True)

con.execute(
    "CREATE OR REPLACE TEMP TABLE sessionized_events AS " + SESSIONIZE_SQL,
    [str(parquet_path), DUPLICATE_GAP_SECONDS, SESSION_GAP_SECONDS],
)
con.execute("CREATE OR REPLACE TEMP TABLE sessions AS " + SESSIONS_SQL)

events_out = (OUTPUT / "sessionized_events_sql.parquet").as_posix()
sessions_out = (OUTPUT / "sessions_sql.parquet").as_posix()
con.execute(f"COPY sessionized_events TO '{events_out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
con.execute(f"COPY sessions TO '{sessions_out}' (FORMAT PARQUET, COMPRESSION ZSTD)")

print(con.execute("SELECT count(*) FROM sessionized_events").fetchone())
print(con.execute("SELECT count(*) FROM sessions").fetchone())
con.close()
```

Parameter bind order for `SESSIONIZE_SQL`:

1. path to `web_events.parquet`  
2. `DUPLICATE_GAP_SECONDS` (2)  
3. `SESSION_GAP_SECONDS` (1800)

### Option C — SQL queries to run in DuckDB

Replace `'day-1/data/web_events.parquet'` with your path. Use `2` for the duplicate window and `1800` for the 30‑minute gap.

**1. Sessionize events** (creates one row per event + `session_id`):

```sql
CREATE OR REPLACE TEMP TABLE sessionized_events AS
WITH raw AS (
    SELECT
        anonymous_id,
        CAST(timestamp AS TIMESTAMP) AS timestamp,
        event_name,
        content_id,
        device_type,
        referrer
    FROM read_parquet('day-1/data/web_events.parquet')
    WHERE anonymous_id IS NOT NULL
      AND timestamp IS NOT NULL
      AND event_name IS NOT NULL
),

-- prior event for near-duplicate detection
ordered AS (
    SELECT
        *,
        lag(timestamp) OVER w AS prev_ts,
        lag(event_name) OVER w AS prev_event,
        lag(COALESCE(CAST(content_id AS VARCHAR), '')) OVER w AS prev_content
    FROM raw
    WINDOW w AS (PARTITION BY anonymous_id ORDER BY timestamp, event_name)
),

-- drop near-duplicates (same event + content within 2 seconds)
deduped AS (
    SELECT
        anonymous_id,
        timestamp,
        event_name,
        content_id,
        device_type,
        referrer
    FROM ordered
    WHERE NOT (
        prev_ts IS NOT NULL
        AND event_name = prev_event
        AND COALESCE(CAST(content_id AS VARCHAR), '') = prev_content
        AND date_diff('second', prev_ts, timestamp) <= 2
    )
),

-- gap to previous kept event
with_gap AS (
    SELECT
        *,
        lag(timestamp) OVER w AS prev_event_ts,
        date_diff('second', lag(timestamp) OVER w, timestamp) AS gap_seconds
    FROM deduped
    WINDOW w AS (PARTITION BY anonymous_id ORDER BY timestamp, event_name)
),

-- new session when first event for cookie OR idle > 30 minutes
flagged AS (
    SELECT
        *,
        CASE
            WHEN prev_event_ts IS NULL OR gap_seconds > 1800 THEN 1
            ELSE 0
        END AS new_session
    FROM with_gap
)

SELECT
    anonymous_id,
    timestamp,
    event_name,
    content_id,
    device_type,
    referrer,
    gap_seconds,
    SUM(new_session) OVER (
        ORDER BY anonymous_id, timestamp, event_name
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )::BIGINT AS session_idx,
    'S' || lpad(
        CAST(
            SUM(new_session) OVER (
                ORDER BY anonymous_id, timestamp, event_name
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS VARCHAR
        ),
        9,
        '0'
    ) AS session_id
FROM flagged
ORDER BY anonymous_id, timestamp, event_name;
```

**2. Session summaries** (one row per visit):

```sql
CREATE OR REPLACE TEMP TABLE sessions AS
SELECT
    session_idx,
    ANY_VALUE(session_id) AS session_id,
    ANY_VALUE(anonymous_id) AS anonymous_id,
    MIN(timestamp) AS session_start,
    MAX(timestamp) AS session_end,
    arg_min(device_type, timestamp) AS device_type,
    arg_min(referrer, timestamp) AS referrer,
    COUNT(*)::BIGINT AS n_events,
    COUNT(DISTINCT content_id)::BIGINT AS n_content
FROM sessionized_events
GROUP BY session_idx
ORDER BY session_idx;
```

**3. Optional checks / export:**

```sql
SELECT count(*) AS n_events FROM sessionized_events;
SELECT count(*) AS n_sessions FROM sessions;
SELECT count(DISTINCT anonymous_id) AS n_cookies FROM sessions;

COPY sessionized_events TO 'day-1/output/sessionized_events_sql.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD);
COPY sessions TO 'day-1/output/sessions_sql.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD);
```

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
