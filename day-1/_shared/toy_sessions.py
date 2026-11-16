"""Tiny shared clickstream for Journey algorithm examples.

Loads from day-1/_shared/data/toy_sessions.csv (regenerate with generate_toy_data.py).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
TOY_SESSIONS_CSV = DATA / "toy_sessions.csv"

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


def load_toy_events() -> pd.DataFrame:
    """Return a mini sessionized event table with stage tags."""
    if not TOY_SESSIONS_CSV.exists():
        raise FileNotFoundError(
            f"missing {TOY_SESSIONS_CSV}. Run: python day-1/_shared/generate_toy_data.py"
        )
    frame = pd.read_csv(TOY_SESSIONS_CSV)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    if "anonymous_id" not in frame.columns:
        frame["anonymous_id"] = frame["session_idx"].map(lambda s: f"A{int(s):04d}")
    if "stage" not in frame.columns:
        frame["stage"] = frame["event_name"].map(STAGE_BY_EVENT)
    else:
        # Keep CSV stage, but fill gaps from the map.
        missing = frame["stage"].isna()
        if missing.any():
            frame.loc[missing, "stage"] = frame.loc[missing, "event_name"].map(STAGE_BY_EVENT)
    return frame


def describe_sessions() -> None:
    print("Toy sessions (4 visits)")
    print(f"  source: {TOY_SESSIONS_CSV.relative_to(DATA.parent.parent)}")
    print("  S1: page_view                         → bounce")
    print("  S2: page_view → scroll → engaged_read → engaged exit")
    print("  S3: … → subscription_view → subscribe_click → intent exit")
    print("  S4: … → checkout → payment → subscription_active → convert")
