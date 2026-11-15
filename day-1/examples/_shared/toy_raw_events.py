"""Raw (pre-session) toy clickstream for the sessionization example.

Designed so learners can verify the 30-minute rule and near-duplicate drop by hand.
"""

from __future__ import annotations

import pandas as pd

# Raw events — NO session_id yet. Gaps and a near-duplicate are intentional.
# Cookie A0001:
#   10:00 page_view
#   10:00:01 page_view same content  → near-duplicate (drop; gap ≤ 2s)
#   10:05 scroll                     → same session (< 30 min)
#   10:40 page_view                  → NEW session (35 min gap)
# Cookie A0002:
#   11:00 page_view → scroll → engaged_read
# Cookie A0003:
#   12:00 … → subscription_view → subscribe_click
# Cookie A0004:
#   13:00 … → checkout → payment → subscription_active (conversion)
_RAW = [
    ("A0001", "2026-01-10 10:00:00", "page_view", "C001", "desktop", "organic_search"),
    ("A0001", "2026-01-10 10:00:01", "page_view", "C001", "desktop", "organic_search"),  # dup
    ("A0001", "2026-01-10 10:05:00", "scroll", "C001", "desktop", None),
    ("A0001", "2026-01-10 10:40:00", "page_view", "C002", "desktop", "direct"),  # new session
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


def load_raw_events() -> pd.DataFrame:
    """Return unsorted-looking raw web events (we sort inside sessionize)."""
    frame = pd.DataFrame(
        _RAW,
        columns=["anonymous_id", "timestamp", "event_name", "content_id", "device_type", "referrer"],
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def describe_raw() -> None:
    print("Raw toy events (before sessionization)")
    print("  A0001: page_view, DUPLICATE page_view (+1s), scroll (+5m), page_view (+35m)")
    print("         → expect 2 sessions after 30-min cut; duplicate dropped")
    print("  A0002: page_view → scroll → engaged_read")
    print("  A0003: … → subscription_view → subscribe_click (intent)")
    print("  A0004: … → checkout → payment → subscription_active (conversion)")
