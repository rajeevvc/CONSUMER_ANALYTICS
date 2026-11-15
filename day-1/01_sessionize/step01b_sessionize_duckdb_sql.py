"""Sessionize web events with DuckDB SQL over Parquet.

Run from repo root:

    python day-1/01_sessionize/step01b_sessionize_duckdb_sql.py

Reads:
    day-1/data/web_events.parquet

Writes:
    day-1/output/sessionized_events_sql.parquet
    day-1/output/sessions_sql.parquet
"""

from __future__ import annotations

from pathlib import Path

import duckdb

DAY1 = Path(__file__).resolve().parents[1]
DATA = DAY1 / "data"
OUTPUT = DAY1 / "output"

WEB_EVENTS_PARQUET = DATA / "web_events.parquet"
WEB_EVENTS_CSV = DATA / "web_events.csv"

SESSION_GAP_SECONDS = 30 * 60
DUPLICATE_GAP_SECONDS = 2

SESSIONIZE_SQL = """
-- 30-minute inactivity sessionization on cookie timelines
WITH raw AS (
    SELECT
        anonymous_id,
        CAST(timestamp AS TIMESTAMP) AS timestamp,
        event_name,
        content_id,
        device_type,
        referrer
    FROM read_parquet(?)
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

-- drop injected 1-second duplicates
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
        AND date_diff('second', prev_ts, timestamp) <= ?
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
            WHEN prev_event_ts IS NULL OR gap_seconds > ? THEN 1
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
ORDER BY anonymous_id, timestamp, event_name
"""

SESSIONS_SQL = """
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
ORDER BY session_idx
"""


def ensure_web_events_parquet(con: duckdb.DuckDBPyConnection) -> Path:
    """Use existing parquet, or build it once from CSV."""
    if WEB_EVENTS_PARQUET.exists():
        return WEB_EVENTS_PARQUET
    if not WEB_EVENTS_CSV.exists():
        raise FileNotFoundError(f"missing {WEB_EVENTS_PARQUET} and {WEB_EVENTS_CSV}")
    DATA.mkdir(parents=True, exist_ok=True)
    csv_sql = WEB_EVENTS_CSV.as_posix().replace("'", "''")
    parquet_sql = WEB_EVENTS_PARQUET.as_posix().replace("'", "''")
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv_auto('{csv_sql}', header := true, sample_size := -1)
        ) TO '{parquet_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    print(f"wrote {WEB_EVENTS_PARQUET}")
    return WEB_EVENTS_PARQUET


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    events_out = OUTPUT / "sessionized_events_sql.parquet"
    sessions_out = OUTPUT / "sessions_sql.parquet"

    con = duckdb.connect()
    try:
        parquet_path = ensure_web_events_parquet(con)

        con.execute(
            "CREATE OR REPLACE TEMP TABLE sessionized_events AS " + SESSIONIZE_SQL,
            [str(parquet_path), DUPLICATE_GAP_SECONDS, SESSION_GAP_SECONDS],
        )
        con.execute("CREATE OR REPLACE TEMP TABLE sessions AS " + SESSIONS_SQL)

        con.execute(
            f"COPY sessionized_events TO '{events_out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        con.execute(
            f"COPY sessions TO '{sessions_out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        n_events, n_sessions, n_cookies = con.execute(
            """
            SELECT
                (SELECT count(*) FROM sessionized_events),
                (SELECT count(*) FROM sessions),
                (SELECT count(DISTINCT anonymous_id) FROM sessions)
            """
        ).fetchone()

        print("DuckDB sessionization over parquet")
        print(f"  source:  {parquet_path}")
        print(f"  events:  {n_events:,}")
        print(f"  sessions:{n_sessions:,}")
        print(f"  cookies: {n_cookies:,}")
        print(f"  wrote {events_out}")
        print(f"  wrote {sessions_out}")

        print("\n-- query used --")
        print(SESSIONIZE_SQL.strip())
    finally:
        con.close()


if __name__ == "__main__":
    main()
