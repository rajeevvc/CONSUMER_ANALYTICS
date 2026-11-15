"""Tiny shared clickstream for Journey algorithm examples.

Four cookies / sessions — small enough to compute by hand on a whiteboard.
"""

from __future__ import annotations

import pandas as pd

# Event → stage (same ladder as Day 1 journey analysis).
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

FUNNEL_STAGES = [
    "landing",
    "scroll",
    "engaged",
    "intent",
    "deep",
    "registration",
    "subscription",
]

# Hand-built journeys (one session each).
# S1: bounce after landing
# S2: read then leave
# S3: intent but no checkout
# S4: full path into checkout + subscribe
_RAW = [
    # session 1 — bounce
    (1, "2026-01-10 10:00:00", "page_view"),
    # session 2 — engaged reader
    (2, "2026-01-10 11:00:00", "page_view"),
    (2, "2026-01-10 11:00:30", "scroll"),
    (2, "2026-01-10 11:01:00", "engaged_read"),
    # session 3 — intent cliff
    (3, "2026-01-10 12:00:00", "page_view"),
    (3, "2026-01-10 12:00:20", "scroll"),
    (3, "2026-01-10 12:01:00", "engaged_read"),
    (3, "2026-01-10 12:02:00", "subscription_view"),
    (3, "2026-01-10 12:02:30", "subscribe_click"),
    # session 4 — converter path
    (4, "2026-01-10 13:00:00", "page_view"),
    (4, "2026-01-10 13:00:15", "scroll"),
    (4, "2026-01-10 13:01:00", "engaged_read"),
    (4, "2026-01-10 13:02:00", "subscription_view"),
    (4, "2026-01-10 13:03:00", "checkout_start"),
    (4, "2026-01-10 13:04:00", "payment_success"),
    (4, "2026-01-10 13:05:00", "subscription_active"),
]


def load_toy_events() -> pd.DataFrame:
    """Return a mini sessionized event table with stage tags."""
    frame = pd.DataFrame(_RAW, columns=["session_idx", "timestamp", "event_name"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["anonymous_id"] = frame["session_idx"].map(lambda s: f"A{s:04d}")
    frame["stage"] = frame["event_name"].map(STAGE_BY_EVENT)
    return frame


def describe_sessions() -> None:
    print("Toy sessions (4 visits)")
    print("  S1: page_view                         → bounce")
    print("  S2: page_view → scroll → engaged_read → engaged exit")
    print("  S3: … → subscription_view → subscribe_click → intent exit")
    print("  S4: … → checkout → payment → subscription_active → convert")
