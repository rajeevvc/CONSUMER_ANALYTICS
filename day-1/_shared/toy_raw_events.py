"""Raw (pre-session) toy clickstream for the sessionization example.

Loads from day-1/_shared/data/toy_raw_events.csv (regenerate with generate_toy_data.py).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
RAW_EVENTS_CSV = DATA / "toy_raw_events.csv"


def load_raw_events() -> pd.DataFrame:
    """Return unsorted-looking raw web events (we sort inside sessionize)."""
    if not RAW_EVENTS_CSV.exists():
        raise FileNotFoundError(
            f"missing {RAW_EVENTS_CSV}. Run: python day-1/_shared/generate_toy_data.py"
        )
    frame = pd.read_csv(RAW_EVENTS_CSV)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def describe_raw() -> None:
    print("Raw toy events (before sessionization)")
    print(f"  source: {RAW_EVENTS_CSV.relative_to(DATA.parent.parent)}")
    print("  A0001: page_view, DUPLICATE page_view (+1s), scroll (+5m), page_view (+35m)")
    print("         → expect 2 sessions after 30-min cut; duplicate dropped")
    print("  A0002: page_view → scroll → engaged_read")
    print("  A0003: … → subscription_view → subscribe_click (intent)")
    print("  A0004: … → checkout → payment → subscription_active (conversion)")
