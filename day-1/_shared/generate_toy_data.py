"""Write example toy tables under day-1/_shared/data/.

Run:
    python day-1/_shared/generate_toy_data.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"

# --- raw (pre-session) clickstream for sessionize example ---
RAW_EVENTS = [
    ("A0001", "2026-01-10 10:00:00", "page_view", "C001", "desktop", "organic_search"),
    ("A0001", "2026-01-10 10:00:01", "page_view", "C001", "desktop", "organic_search"),
    ("A0001", "2026-01-10 10:05:00", "scroll", "C001", "desktop", None),
    ("A0001", "2026-01-10 10:40:00", "page_view", "C002", "desktop", "direct"),
    ("A0002", "2026-01-10 11:00:00", "page_view", "C010", "mobile", "social_organic"),
    ("A0002", "2026-01-10 11:00:30", "scroll", "C010", "mobile", None),
    ("A0002", "2026-01-10 11:01:00", "engaged_read", "C010", "mobile", None),
    ("A0003", "2026-01-10 12:00:00", "page_view", "C020", "tablet", "email"),
    ("A0003", "2026-01-10 12:00:20", "scroll", "C020", "tablet", None),
    ("A0003", "2026-01-10 12:01:00", "engaged_read", "C020", "tablet", None),
    ("A0003", "2026-01-10 12:02:00", "subscription_view", "C020", "tablet", None),
    ("A0003", "2026-01-10 12:02:30", "subscribe_click", "C020", "tablet", None),
    ("A0004", "2026-01-10 13:00:00", "page_view", "C030", "desktop", "organic_search"),
    ("A0004", "2026-01-10 13:00:15", "scroll", "C030", "desktop", None),
    ("A0004", "2026-01-10 13:01:00", "engaged_read", "C030", "desktop", None),
    ("A0004", "2026-01-10 13:02:00", "subscription_view", "C030", "desktop", None),
    ("A0004", "2026-01-10 13:03:00", "checkout_start", "C030", "desktop", None),
    ("A0004", "2026-01-10 13:04:00", "payment_success", "C030", "desktop", None),
    ("A0004", "2026-01-10 13:05:00", "subscription_active", None, "desktop", None),
]

# --- already-sessionized journeys for Funnel / Markov / DFG / HMM / features ---
TOY_SESSIONS = [
    (1, "2026-01-10 10:00:00", "page_view"),
    (2, "2026-01-10 11:00:00", "page_view"),
    (2, "2026-01-10 11:00:30", "scroll"),
    (2, "2026-01-10 11:01:00", "engaged_read"),
    (3, "2026-01-10 12:00:00", "page_view"),
    (3, "2026-01-10 12:00:20", "scroll"),
    (3, "2026-01-10 12:01:00", "engaged_read"),
    (3, "2026-01-10 12:02:00", "subscription_view"),
    (3, "2026-01-10 12:02:30", "subscribe_click"),
    (4, "2026-01-10 13:00:00", "page_view"),
    (4, "2026-01-10 13:00:15", "scroll"),
    (4, "2026-01-10 13:01:00", "engaged_read"),
    (4, "2026-01-10 13:02:00", "subscription_view"),
    (4, "2026-01-10 13:03:00", "checkout_start"),
    (4, "2026-01-10 13:04:00", "payment_success"),
    (4, "2026-01-10 13:05:00", "subscription_active"),
]

STAGE_BY_EVENT = {
    "page_view": "landing",
    "scroll": "scroll",
    "engaged_read": "engaged",
    "subscription_view": "intent",
    "subscribe_click": "intent",
    "checkout_start": "deep",
    "payment_success": "deep",
    "register_complete": "registration",
    "subscription_active": "subscription",
}


def toy_audience_rows() -> list[dict]:
    rows = []
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"B{i + 1}",
                "persona": "bouncer_truth",
                "n_sessions": 1,
                "mean_duration_sec": 20 + i * 5,
                "mean_furthest_rank": 1.0,
                "share_intent": 0.0,
                "share_deep": 0.0,
                "subscription_view_rate": 0.0,
                "conversion_rate": 0.0,
            }
        )
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"R{i + 1}",
                "persona": "reader_truth",
                "n_sessions": 2 + i,
                "mean_duration_sec": 180 + i * 20,
                "mean_furthest_rank": 3.0 + 0.2 * i,
                "share_intent": 0.1,
                "share_deep": 0.0,
                "subscription_view_rate": 0.05,
                "conversion_rate": 0.0,
            }
        )
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"C{i + 1}",
                "persona": "converter_truth",
                "n_sessions": 3 + i,
                "mean_duration_sec": 400 + i * 30,
                "mean_furthest_rank": 4.5 + 0.1 * i,
                "share_intent": 0.4,
                "share_deep": 0.3,
                "subscription_view_rate": 0.25,
                "conversion_rate": 0.4 + 0.1 * i,
            }
        )
    return rows


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    raw = pd.DataFrame(
        RAW_EVENTS,
        columns=["anonymous_id", "timestamp", "event_name", "content_id", "device_type", "referrer"],
    )
    raw_path = DATA / "toy_raw_events.csv"
    raw.to_csv(raw_path, index=False)

    sessions = pd.DataFrame(TOY_SESSIONS, columns=["session_idx", "timestamp", "event_name"])
    sessions["anonymous_id"] = sessions["session_idx"].map(lambda s: f"A{s:04d}")
    sessions["stage"] = sessions["event_name"].map(STAGE_BY_EVENT)
    sessions_path = DATA / "toy_sessions.csv"
    sessions.to_csv(sessions_path, index=False)

    audience = pd.DataFrame(toy_audience_rows())
    audience_path = DATA / "toy_audience.csv"
    audience.to_csv(audience_path, index=False)

    print(f"wrote {raw_path} ({len(raw)} rows)")
    print(f"wrote {sessions_path} ({len(sessions)} rows)")
    print(f"wrote {audience_path} ({len(audience)} rows)")


if __name__ == "__main__":
    main()
