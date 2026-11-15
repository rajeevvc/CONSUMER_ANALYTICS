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
    print("Goal: turn event streams into numeric vectors for segmentation.")
    describe_sessions()
    events = load_toy_events()

    print("\nTransform steps")
    print("  1. Build one SESSION row: duration, furthest stage, event counts, converted")
    print("  2. Roll up to one USER (cookie) row:")
    print("       frequency  = n_sessions, days_active")
    print("       recency    = days since last session")
    print("       engagement = mean duration / depth / event rates")
    print("       outcome    = conversion_rate")

    sessions = session_features(events)
    users = user_features(sessions)

    _section("OUTPUT 1 — Session features")
    print("Column meanings")
    print("  session_idx / anonymous_id  visit id and cookie")
    print("  duration_sec                last_ts − first_ts inside the session")
    print("  n_behavior_events           count of browsing events in the visit")
    print("  furthest_stage              deepest funnel stage touched")
    print("  converted                   1 if subscription/payment outcome occurred")
    print("  page_view / scroll / …      raw event counts")
    cols = [
        "session_idx",
        "anonymous_id",
        "duration_sec",
        "n_behavior_events",
        "furthest_stage",
        "converted",
        "page_view",
        "scroll",
        "engaged_read",
    ]
    print("\nFull session table")
    print(sessions[cols].to_string(index=False))
    print("\nRow-by-row")
    for row in sessions.itertuples(index=False):
        print(f"  S{row.session_idx} ({row.anonymous_id}): "
              f"duration={row.duration_sec:.0f}s, events={row.n_behavior_events}, "
              f"furthest={row.furthest_stage}, converted={int(row.converted)}")

    _section("OUTPUT 2 — User features (cookie grain)")
    print("Column meanings")
    print("  n_sessions            visits for this cookie")
    print("  mean_duration_sec     average session length")
    print("  mean_furthest_rank    average depth (landing=1 … deep=5)")
    print("  share_intent/deep     fraction of sessions that reached those stages")
    print("  *_rate                event mix / outcome rates across sessions")
    print("  recency_days          days since last session (0 in single-day toy)")
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
    print("\nFull user table")
    print(users[preview].round(3).to_string(index=False))
    print("\nRow-by-row")
    for row in users.itertuples(index=False):
        print(f"  {row.anonymous_id}: sessions={row.n_sessions}, "
              f"mean_depth={row.mean_furthest_rank:.1f}, "
              f"share_deep={row.share_deep:.2f}, "
              f"conversion_rate={row.conversion_rate:.2f}")

    _section("OUTPUT 3 — Acceptance checks")
    print("  Each toy cookie has 1 session → n_sessions = 1")
    print(f"  n_sessions unique values = {sorted(users['n_sessions'].unique().tolist())}")
    a4 = users.loc[users["anonymous_id"] == "A0004"].iloc[0]
    a1 = users.loc[users["anonymous_id"] == "A0001"].iloc[0]
    print(f"  A0004 conversion_rate = {a4.conversion_rate}  (expect 1.0)")
    print(f"  A0001 mean_furthest_rank = {a1.mean_furthest_rank}  (expect 1.0 landing)")
    print(f"  A0004 mean_furthest_rank = {a4.mean_furthest_rank}  (expect 5.0 deep)")

    _section("Teaching takeaway")
    print("  Features bridge visits → audience vectors for segmentation.")


if __name__ == "__main__":
    main()
