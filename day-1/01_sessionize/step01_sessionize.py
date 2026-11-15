"""Day 1 — Event collection + sessionization (30-minute inactivity rule).

Single self-contained script. Run from anywhere:

    python day-1/01_sessionize/step01_sessionize.py

Reads the regenerated clickstream under day-1/data (new event taxonomy),
drops near-duplicate rows, cuts sessions at 30 minutes of inactivity, attaches a
7-day register/subscribe label, and writes:

    day-1/output/sessionized_events.csv
    day-1/output/sessions.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DAY1 = Path(__file__).resolve().parents[1]
DATA = DAY1 / "data"
OUTPUT = DAY1 / "output"

WEB_EVENTS = DATA / "web_events.csv"
APP_EVENTS = DATA / "app_events.csv"
CONTENT = DATA / "content_catalog.csv"
SUBSCRIPTIONS = DATA / "subscriptions.csv"

# Columns present in the regenerated web_events.csv
WEB_COLUMNS = [
    "event_id",
    "anonymous_id",
    "timestamp",
    "event_name",
    "device_type",
    "session_id",
    "content_id",
    "referrer",
]
WEB_USECOLS = ["anonymous_id", "timestamp", "event_name", "content_id", "device_type", "referrer"]

SESSION_GAP_SECONDS = 30 * 60
DUPLICATE_GAP_SECONDS = 2
HORIZON_DAYS = 7

CONVERSION_EVENTS = {"register_complete", "subscription_active"}
STAGE_BY_EVENT = {
    "page_view": "landing",
    "login": "landing",
    "scroll": "scroll",
    "engaged_read": "engaged",
    "share": "intent",
    "subscription_view": "intent",
    "subscribe_click": "intent",
    "checkout_start": "deep",
    "payment_success": "deep",
    "register_start": "registration",
    "register_complete": "registration",
    "subscription_active": "subscription",
}
# Behavior depth ladder used for furthest_stage (registration/subscription are outcomes).
STAGE_RANK = {
    "landing": 1,
    "scroll": 2,
    "engaged": 3,
    "intent": 4,
    "deep": 5,
}
BEHAVIOR_EVENTS = [
    "page_view",
    "scroll",
    "engaged_read",
    "share",
    "login",
    "register_start",
    "subscription_view",
    "subscribe_click",
    "checkout_start",
    "payment_success",
]
KNOWN_EVENTS = set(STAGE_BY_EVENT)


# ---------------------------------------------------------------------------
# 1. Event collection
# ---------------------------------------------------------------------------


def collect_inventory() -> dict[str, int]:
    """Confirm Web / App / Content / Subscription sources are present."""
    inventory = {
        "web_events": _row_count(WEB_EVENTS),
        "app_events": _row_count(APP_EVENTS),
        "content_catalog": _row_count(CONTENT),
        "subscriptions": _row_count(SUBSCRIPTIONS),
    }
    missing = [name for name, rows in inventory.items() if rows is None]
    if missing:
        raise FileNotFoundError(f"missing raw tables: {', '.join(missing)} under {DATA}")
    return {name: int(rows) for name, rows in inventory.items()}


def load_web_events() -> pd.DataFrame:
    """Load the regenerated web clickstream used for Day 1 sessionization.

    The raw file already has a generator session_id; Day 1 ignores it and
    rebuilds sessions with the 30-minute rule.
    """
    _validate_web_header()
    events = pd.read_csv(
        WEB_EVENTS,
        usecols=WEB_USECOLS,
        dtype={
            "anonymous_id": "string",
            "event_name": "string",
            "content_id": "string",
            "device_type": "string",
            "referrer": "string",
        },
    )
    events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce")
    events = events.dropna(subset=["anonymous_id", "timestamp", "event_name"])
    events["anonymous_id"] = events["anonymous_id"].astype(str)
    events["event_name"] = events["event_name"].astype(str)

    unknown = sorted(set(events["event_name"].unique()) - KNOWN_EVENTS)
    if unknown:
        raise ValueError(
            "web_events.csv has unexpected event_name values: "
            + ", ".join(unknown)
            + ". Update STAGE_BY_EVENT / BEHAVIOR_EVENTS in step01_sessionize.py."
        )

    events = events.sort_values(["anonymous_id", "timestamp"], kind="mergesort")
    events = _drop_near_duplicates(events)
    events["stage"] = events["event_name"].map(STAGE_BY_EVENT).fillna("landing")
    events["is_conversion"] = events["event_name"].isin(CONVERSION_EVENTS)
    return events.reset_index(drop=True)


def _validate_web_header() -> None:
    if not WEB_EVENTS.exists():
        raise FileNotFoundError(f"missing {WEB_EVENTS}")
    header = pd.read_csv(WEB_EVENTS, nrows=0)
    missing = [column for column in WEB_USECOLS if column not in header.columns]
    if missing:
        raise ValueError(
            f"{WEB_EVENTS.name} is missing columns {missing}. "
            f"Expected at least {WEB_USECOLS}. Found {list(header.columns)}."
        )


def _row_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _drop_near_duplicates(events: pd.DataFrame) -> pd.DataFrame:
    content_key = events["content_id"].fillna("")
    gap = events.groupby("anonymous_id", sort=False)["timestamp"].diff().dt.total_seconds()
    near_duplicate = (
        events["anonymous_id"].eq(events["anonymous_id"].shift())
        & events["event_name"].eq(events["event_name"].shift())
        & content_key.eq(content_key.shift())
        & gap.le(DUPLICATE_GAP_SECONDS)
    )
    return events.loc[~near_duplicate.fillna(False)].copy()


# ---------------------------------------------------------------------------
# 2. Sessionization — 30-minute inactivity rule
# ---------------------------------------------------------------------------


def sessionize(events: pd.DataFrame, gap_seconds: int = SESSION_GAP_SECONDS) -> pd.DataFrame:
    """Start a new session when the gap since the prior event for that cookie exceeds 30 minutes."""
    events = events.sort_values(["anonymous_id", "timestamp"], kind="mergesort").reset_index(drop=True)
    gap = events.groupby("anonymous_id", sort=False)["timestamp"].diff().dt.total_seconds()
    new_session = gap.isna() | gap.gt(gap_seconds)
    session_idx = new_session.to_numpy().cumsum().astype(np.int64)
    out = events.copy()
    out["session_idx"] = session_idx
    out["session_id"] = np.char.add("S", np.char.zfill(session_idx.astype(str), 9))
    out["gap_seconds"] = gap
    return out


def session_summary(events: pd.DataFrame) -> pd.DataFrame:
    """One row per session with landing context and behavior counts."""
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
    behavior_stats = behavior.groupby("session_idx", sort=False).agg(
        behavior_start=("timestamp", "min"),
        behavior_end=("timestamp", "max"),
        n_behavior_events=("event_name", "size"),
        n_content=("content_id", "nunique"),
        furthest_rank=("stage_rank", "max"),
    )
    behavior_stats["furthest_stage"] = behavior_stats["furthest_rank"].map(
        {rank: stage for stage, rank in STAGE_RANK.items()}
    )
    counts = behavior.groupby(["session_idx", "event_name"], sort=False).size().unstack(fill_value=0)
    summary = summary.join(behavior_stats, how="left").join(counts, how="left")

    summary["n_behavior_events"] = summary["n_behavior_events"].fillna(0).astype(np.int64)
    summary["n_content"] = summary["n_content"].fillna(0).astype(np.int64)
    summary["duration_sec"] = (
        (summary["behavior_end"] - summary["behavior_start"]).dt.total_seconds().fillna(0).clip(lower=0)
    )
    summary["device_type"] = summary["device_type"].fillna("unknown")
    summary["referrer"] = summary["referrer"].fillna("unknown")
    for name in BEHAVIOR_EVENTS:
        if name not in summary.columns:
            summary[name] = 0
        summary[name] = summary[name].fillna(0).astype(np.int64)
    summary["furthest_stage"] = summary["furthest_stage"].fillna("none")
    summary["furthest_rank"] = summary["furthest_rank"].fillna(0).astype(np.int64)
    return summary.reset_index()


def attach_conversion_label(
    sessions: pd.DataFrame, events: pd.DataFrame, horizon_days: int = HORIZON_DAYS
) -> pd.DataFrame:
    """Label a browsing session if that cookie registers or activates within the horizon."""
    conversions = events.loc[events["is_conversion"], ["anonymous_id", "timestamp"]].sort_values(
        ["anonymous_id", "timestamp"], kind="mergesort"
    )
    conversion_times = {
        anonymous_id: times.to_numpy(dtype="datetime64[ns]")
        for anonymous_id, times in conversions.groupby("anonymous_id", sort=False)["timestamp"]
    }
    horizon = np.timedelta64(horizon_days, "D")
    labels = np.zeros(len(sessions), dtype=bool)
    already = np.zeros(len(sessions), dtype=bool)
    positions = pd.Series(np.arange(len(sessions)), index=sessions.index)

    for anonymous_id, group in sessions.groupby("anonymous_id", sort=False):
        times = conversion_times.get(anonymous_id)
        if times is None or len(times) == 0:
            continue
        starts = group["session_start"].to_numpy(dtype="datetime64[ns]")
        next_index = np.searchsorted(times, starts, side="left")
        row = positions.loc[group.index].to_numpy()
        already[row] = next_index > 0
        has_next = next_index < len(times)
        first_conversion = has_next & (next_index == 0)
        if not first_conversion.any():
            continue
        upcoming = times[next_index[first_conversion]]
        labels[row[first_conversion]] = (upcoming - starts[first_conversion]) <= horizon

    labeled = sessions.copy()
    labeled["converted"] = labels
    labeled["already_converted"] = already
    return labeled


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    inventory = collect_inventory()
    print("1. Event Collection — Web / App / Content / Subscription")
    for name, rows in inventory.items():
        print(f"   {name}: {rows:,}")

    print("\n2. Sessionization — 30-minute inactivity rule")
    events = sessionize(load_web_events())
    sessions = attach_conversion_label(session_summary(events), events)

    events_csv = OUTPUT / "sessionized_events.csv"
    sessions_csv = OUTPUT / "sessions.csv"
    events.to_csv(events_csv, index=False)
    sessions.to_csv(sessions_csv, index=False)

    open_sessions = sessions["n_behavior_events"].gt(0) & ~sessions["already_converted"]
    print(f"   events: {len(events):,}")
    print(f"   sessions: {sessions['session_id'].nunique():,}")
    print(f"   cookies: {sessions['anonymous_id'].nunique():,}")
    print(f"   still anonymous: {int(open_sessions.sum()):,}")
    print(f"   convert within 7 days: {sessions.loc[open_sessions, 'converted'].mean():.2%}")
    print("   event mix:")
    for name, count in events["event_name"].value_counts().items():
        print(f"      {name}: {count:,}")
    print("   furthest stage:")
    for stage, count in sessions["furthest_stage"].value_counts().items():
        print(f"      {stage}: {count:,}")
    print(f"\nwrote {events_csv}")
    print(f"wrote {sessions_csv}")


if __name__ == "__main__":
    main()
