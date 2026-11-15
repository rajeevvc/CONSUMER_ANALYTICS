"""Sessionization example — 30-minute inactivity rule.

Question: How do raw clicks become visits (sessions)?

Run:
    python day-1/examples/01_sessionize/01_sessionize_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_EXAMPLES = Path(__file__).resolve().parents[1]
_SHARED = _EXAMPLES / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from toy_raw_events import describe_raw, load_raw_events

SESSION_GAP_SECONDS = 30 * 60
DUPLICATE_GAP_SECONDS = 2
HORIZON_DAYS = 7
CONVERSION_EVENTS = {"register_complete", "subscription_active"}
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
STAGE_RANK = {"landing": 1, "scroll": 2, "engaged": 3, "intent": 4, "deep": 5}


def drop_near_duplicates(events: pd.DataFrame) -> pd.DataFrame:
    events = events.sort_values(["anonymous_id", "timestamp"], kind="mergesort")
    content_key = events["content_id"].fillna("")
    gap = events.groupby("anonymous_id", sort=False)["timestamp"].diff().dt.total_seconds()
    near_duplicate = (
        events["anonymous_id"].eq(events["anonymous_id"].shift())
        & events["event_name"].eq(events["event_name"].shift())
        & content_key.eq(content_key.shift())
        & gap.le(DUPLICATE_GAP_SECONDS)
    )
    return events.loc[~near_duplicate.fillna(False)].copy()


def sessionize(events: pd.DataFrame) -> pd.DataFrame:
    events = events.sort_values(["anonymous_id", "timestamp"], kind="mergesort").reset_index(drop=True)
    gap = events.groupby("anonymous_id", sort=False)["timestamp"].diff().dt.total_seconds()
    new_session = gap.isna() | gap.gt(SESSION_GAP_SECONDS)
    session_idx = new_session.to_numpy().cumsum().astype(np.int64)
    out = events.copy()
    out["gap_seconds"] = gap
    out["session_idx"] = session_idx
    out["session_id"] = np.char.add("S", np.char.zfill(session_idx.astype(str), 9))
    out["stage"] = out["event_name"].map(STAGE_BY_EVENT).fillna("landing")
    out["is_conversion"] = out["event_name"].isin(CONVERSION_EVENTS)
    return out


def session_summary(events: pd.DataFrame) -> pd.DataFrame:
    behavior = events.loc[~events["is_conversion"]].copy()
    behavior["stage_rank"] = behavior["stage"].map(STAGE_RANK).fillna(0)
    summary = events.groupby("session_idx", sort=False).agg(
        session_id=("session_id", "first"),
        anonymous_id=("anonymous_id", "first"),
        session_start=("timestamp", "min"),
        session_end=("timestamp", "max"),
        device_type=("device_type", "first"),
        referrer=("referrer", "first"),
        n_events=("event_name", "size"),
    )
    stats = behavior.groupby("session_idx", sort=False).agg(
        n_behavior_events=("event_name", "size"),
        furthest_rank=("stage_rank", "max"),
        behavior_start=("timestamp", "min"),
        behavior_end=("timestamp", "max"),
    )
    stats["furthest_stage"] = stats["furthest_rank"].map({v: k for k, v in STAGE_RANK.items()})
    stats["duration_sec"] = (
        (stats["behavior_end"] - stats["behavior_start"]).dt.total_seconds().fillna(0).clip(lower=0)
    )
    return summary.join(stats, how="left").reset_index()


def attach_conversion_label(sessions: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    conversions = events.loc[events["is_conversion"], ["anonymous_id", "timestamp"]].sort_values(
        ["anonymous_id", "timestamp"]
    )
    conversion_times = {
        cookie: times.to_numpy(dtype="datetime64[ns]")
        for cookie, times in conversions.groupby("anonymous_id", sort=False)["timestamp"]
    }
    horizon = np.timedelta64(HORIZON_DAYS, "D")
    labels = np.zeros(len(sessions), dtype=bool)
    already = np.zeros(len(sessions), dtype=bool)
    positions = pd.Series(np.arange(len(sessions)), index=sessions.index)

    for cookie, group in sessions.groupby("anonymous_id", sort=False):
        times = conversion_times.get(cookie)
        if times is None or len(times) == 0:
            continue
        starts = group["session_start"].to_numpy(dtype="datetime64[ns]")
        next_index = np.searchsorted(times, starts, side="left")
        row = positions.loc[group.index].to_numpy()
        already[row] = next_index > 0
        first_conversion = (next_index == 0) & (next_index < len(times))
        if not first_conversion.any():
            continue
        upcoming = times[next_index[first_conversion]]
        labels[row[first_conversion]] = (upcoming - starts[first_conversion]) <= horizon

    out = sessions.copy()
    out["converted"] = labels
    out["already_converted"] = already
    return out


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("SESSIONIZE — 30-minute inactivity rule")
    print("Goal: raw clicks → one scorecard row per visit (session).")
    describe_raw()

    raw = load_raw_events().sort_values(["anonymous_id", "timestamp"], kind="mergesort")
    _section("RAW — input events")
    print(
        raw[["anonymous_id", "timestamp", "event_name", "content_id", "device_type", "referrer"]].to_string(
            index=False
        )
    )

    cleaned = drop_near_duplicates(raw)
    events = sessionize(cleaned)
    sessions = attach_conversion_label(session_summary(events), events)

    _section("PROCESSED — session summary (one row per visit)")
    print(
        sessions[
            [
                "session_id",
                "anonymous_id",
                "session_start",
                "duration_sec",
                "n_behavior_events",
                "furthest_stage",
                "converted",
            ]
        ].to_string(index=False)
    )
    print(
        f"\nNote: {len(raw)} raw events → {len(cleaned)} after 2s dedupe → "
        f"{len(sessions)} sessions (30-min gap). "
        f"A0001 splits into 2 visits; only S000000005 converted."
    )


if __name__ == "__main__":
    main()
