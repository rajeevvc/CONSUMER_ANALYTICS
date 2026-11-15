"""Feature-engineering example — session → user vectors.

Question: How do we turn visits into one feature row per cookie?

Run:
    python day-1/examples/04_feature_engineering/01_feature_engineering_example.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pathlib import Path
import sys
_EXAMPLES = Path(__file__).resolve().parents[1]
_SHARED = _EXAMPLES / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
from toy_sessions import STAGE_BY_EVENT, describe_sessions, load_toy_events

STAGE_RANK = {"landing": 1, "scroll": 2, "engaged": 3, "intent": 4, "deep": 5}
BEHAVIOR = [
    "page_view",
    "scroll",
    "engaged_read",
    "subscription_view",
    "subscribe_click",
    "checkout_start",
    "payment_success",
]
CONVERSION = {"subscription_active", "register_complete"}


def session_features(events: pd.DataFrame) -> pd.DataFrame:
    """One row per session — same spirit as step01 summary + step04 enrich."""
    work = events.copy()
    work["stage"] = work["event_name"].map(STAGE_BY_EVENT)
    work["is_conversion"] = work["event_name"].isin(CONVERSION)
    behavior = work.loc[~work["is_conversion"]].copy()
    behavior["stage_rank"] = behavior["stage"].map(STAGE_RANK).fillna(0)

    rows = []
    for session_idx, part in work.groupby("session_idx", sort=True):
        beh = behavior.loc[behavior["session_idx"] == session_idx]
        counts = beh["event_name"].value_counts()
        start = part["timestamp"].min()
        end = beh["timestamp"].max() if len(beh) else start
        furthest_rank = int(beh["stage_rank"].max()) if len(beh) else 0
        furthest_stage = {v: k for k, v in STAGE_RANK.items()}.get(furthest_rank, "none")
        row = {
            "session_idx": int(session_idx),
            "anonymous_id": part["anonymous_id"].iloc[0],
            "session_start": start,
            "duration_sec": float((end - beh["timestamp"].min()).total_seconds()) if len(beh) else 0.0,
            "n_behavior_events": int(len(beh)),
            "furthest_rank": furthest_rank,
            "furthest_stage": furthest_stage,
            "converted": bool(part["is_conversion"].any()),
        }
        for name in BEHAVIOR:
            row[name] = int(counts.get(name, 0))
        rows.append(row)
    return pd.DataFrame(rows)


def user_features(sessions: pd.DataFrame) -> pd.DataFrame:
    """One row per cookie — same spirit as step04_feature_engineering.user_features."""
    grouped = sessions.groupby("anonymous_id", sort=False)
    features = grouped.agg(
        n_sessions=("session_idx", "nunique"),
        mean_duration_sec=("duration_sec", "mean"),
        mean_behavior_events=("n_behavior_events", "mean"),
        mean_furthest_rank=("furthest_rank", "mean"),
        conversion_rate=("converted", "mean"),
        first_session=("session_start", "min"),
        last_session=("session_start", "max"),
    )
    stage = sessions.groupby(["anonymous_id", "furthest_stage"], sort=False).size().unstack(fill_value=0)
    for col in ["landing", "scroll", "engaged", "intent", "deep", "none"]:
        if col not in stage.columns:
            stage[col] = 0
    totals = stage.sum(axis=1).replace(0, np.nan)
    features["share_intent"] = (stage["intent"] / totals).fillna(0.0)
    features["share_deep"] = (stage["deep"] / totals).fillna(0.0)
    features["share_landing_or_scroll"] = ((stage["landing"] + stage["scroll"]) / totals).fillna(0.0)

    event_totals = sessions.groupby("anonymous_id", sort=False)[BEHAVIOR].sum()
    behavior_sum = sessions.groupby("anonymous_id", sort=False)["n_behavior_events"].sum().replace(0, np.nan)
    for name in BEHAVIOR:
        features[f"{name}_rate"] = (event_totals[name] / behavior_sum).fillna(0.0)

    features["days_active"] = (features["last_session"] - features["first_session"]).dt.total_seconds() / 86400.0
    snapshot = features["last_session"].max()
    features["recency_days"] = (snapshot - features["last_session"]).dt.total_seconds() / 86400.0
    return features.reset_index()


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("FEATURE ENGINEERING — session → user")
    print("Goal: raw events → one numeric vector per cookie.")
    describe_sessions()
    events = load_toy_events()

    _section("RAW — input events")
    print(events[["session_idx", "anonymous_id", "timestamp", "event_name", "stage"]].to_string(index=False))

    sessions = session_features(events)
    users = user_features(sessions)
    preview = [
        "anonymous_id",
        "n_sessions",
        "mean_duration_sec",
        "mean_furthest_rank",
        "share_intent",
        "share_deep",
        "subscription_view_rate",
        "conversion_rate",
        "recency_days",
    ]
    _section("PROCESSED — user features (cookie grain)")
    print(users[preview].round(3).to_string(index=False))
    print("\nNote: A0001 depth=1 / convert=0; A0004 depth=5 / convert=1.0 (ready for segmentation).")


if __name__ == "__main__":
    main()
