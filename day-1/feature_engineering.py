"""Day 1 — Feature Engineering: Session → User-level features.

Single self-contained script. Run after sessionization (HMM optional):

    python day-1/sessionize.py
    python day-1/behavioral_state_modeling.py   # optional, adds mode shares
    python day-1/feature_engineering.py

Reads CSV only. Rolls session rows up to one feature vector per anonymous_id.
Writes:

    day-1/output/session_features.csv
    day-1/output/user_features.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
SESSIONS = OUTPUT / "sessions.csv"
EVENTS_HMM = OUTPUT / "sessionized_events_hmm.csv"

# Keep in sync with day-1/sessionize.py behavior event counts.
EVENT_COLUMNS = [
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
REQUIRED_SESSION_COLUMNS = [
    "session_idx",
    "session_id",
    "anonymous_id",
    "session_start",
    "session_end",
    "device_type",
    "referrer",
    "n_behavior_events",
    "n_content",
    "furthest_rank",
    "furthest_stage",
    "duration_sec",
    "converted",
    "already_converted",
]
USER_FEATURE_COLUMNS = [
    "n_sessions",
    "mean_duration_sec",
    "mean_behavior_events",
    "mean_content",
    "mean_furthest_rank",
    "share_deep",
    "share_intent",
    "share_engaged",
    "share_landing_or_scroll",
    "page_view_rate",
    "scroll_rate",
    "engaged_read_rate",
    "share_rate",
    "login_rate",
    "register_start_rate",
    "subscription_view_rate",
    "subscribe_click_rate",
    "checkout_start_rate",
    "payment_success_rate",
    "conversion_rate",
    "share_desktop",
    "share_mobile",
    "share_tablet",
    "n_devices",
    "n_referrers",
    "days_active",
    "recency_days",
]


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_sessions() -> pd.DataFrame:
    """Load sessions.csv from sessionize.py; rebuild if missing."""
    if SESSIONS.exists():
        sessions = pd.read_csv(SESSIONS)
    else:
        from sessionize import attach_conversion_label, load_web_events, session_summary, sessionize

        print("sessions.csv missing — rebuilding sessions")
        events = sessionize(load_web_events())
        sessions = attach_conversion_label(session_summary(events), events)

    missing = [column for column in REQUIRED_SESSION_COLUMNS if column not in sessions.columns]
    if missing:
        raise ValueError(
            f"{SESSIONS.name} missing columns: {', '.join(missing)}. "
            "Re-run python day-1/sessionize.py with the regenerated web_events.csv."
        )

    sessions["session_start"] = pd.to_datetime(sessions["session_start"], errors="coerce")
    sessions["session_end"] = pd.to_datetime(sessions["session_end"], errors="coerce")
    sessions = sessions.dropna(subset=["anonymous_id", "session_start", "session_idx"]).copy()
    sessions["session_idx"] = sessions["session_idx"].astype(np.int64)
    sessions["converted"] = _as_bool(sessions["converted"])
    sessions["already_converted"] = _as_bool(sessions["already_converted"])
    return sessions


def enrich_session_features(sessions: pd.DataFrame) -> pd.DataFrame:
    """Session-grain features used downstream and as the rollup source."""
    frame = sessions.copy()
    for name in EVENT_COLUMNS:
        if name not in frame.columns:
            frame[name] = 0
        frame[name] = pd.to_numeric(frame[name], errors="coerce").fillna(0).astype(np.int64)

    frame["duration_sec"] = pd.to_numeric(frame["duration_sec"], errors="coerce").fillna(0).clip(lower=0)
    frame["n_behavior_events"] = pd.to_numeric(frame["n_behavior_events"], errors="coerce").fillna(0).astype(np.int64)
    frame["n_content"] = pd.to_numeric(frame["n_content"], errors="coerce").fillna(0).astype(np.int64)
    frame["furthest_rank"] = pd.to_numeric(frame["furthest_rank"], errors="coerce").fillna(0).astype(np.int64)
    frame["device_type"] = frame["device_type"].fillna("unknown").astype(str)
    frame["referrer"] = frame["referrer"].fillna("unknown").astype(str)
    frame["furthest_stage"] = frame["furthest_stage"].fillna("none").astype(str)

    starts = frame.groupby("anonymous_id", sort=False)["session_start"]
    frame["prior_sessions"] = starts.cumcount()
    first_start = starts.transform("min")
    frame["days_since_first_session"] = (frame["session_start"] - first_start).dt.total_seconds() / 86400.0
    frame["start_hour"] = frame["session_start"].dt.hour
    frame["start_dow"] = frame["session_start"].dt.dayofweek
    frame["is_weekend"] = frame["start_dow"].isin([5, 6]).astype(np.int8)
    frame["deep_session"] = frame["furthest_stage"].eq("deep").astype(np.int8)
    frame["intent_session"] = frame["furthest_stage"].isin(["intent", "deep"]).astype(np.int8)
    frame["engaged_or_deeper"] = frame["furthest_rank"].ge(3).astype(np.int8)

    hmm_shares = _hmm_session_shares()
    if hmm_shares is not None:
        frame = frame.merge(hmm_shares, on="session_idx", how="left")
        for column in hmm_shares.columns:
            if column == "session_idx":
                continue
            if column == "hmm_dominant_mode":
                frame[column] = frame[column].fillna("")
            else:
                frame[column] = frame[column].fillna(0.0)
    return frame


def _hmm_session_shares() -> pd.DataFrame | None:
    """Optional mode mix from behavioral_state_modeling.py CSV output."""
    if not EVENTS_HMM.exists():
        return None
    events = pd.read_csv(EVENTS_HMM, usecols=["session_idx", "hmm_mode", "event_name", "is_conversion"])
    events["session_idx"] = events["session_idx"].astype(np.int64)
    if "is_conversion" in events.columns:
        is_conversion = _as_bool(events["is_conversion"])
    else:
        is_conversion = events["event_name"].isin(["register_complete", "subscription_active"])
    work = events.loc[~is_conversion & events["hmm_mode"].fillna("").astype(str).ne("")]
    if work.empty:
        return None
    counts = work.groupby(["session_idx", "hmm_mode"], sort=False).size().unstack(fill_value=0)
    shares = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    shares = shares.rename(columns={mode: f"hmm_share_{mode}" for mode in shares.columns})
    shares["hmm_dominant_mode"] = counts.idxmax(axis=1)
    return shares.reset_index()


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes", "y", "t"])
    )


# ---------------------------------------------------------------------------
# Session → User
# ---------------------------------------------------------------------------


def user_features(sessions: pd.DataFrame) -> pd.DataFrame:
    """One row per anonymous_id from session features."""
    work = sessions.loc[sessions["n_behavior_events"].gt(0)].copy()
    if work.empty:
        raise RuntimeError("no behavior sessions available for user features")

    grouped = work.groupby("anonymous_id", sort=False)
    features = grouped.agg(
        n_sessions=("session_id", "nunique"),
        mean_duration_sec=("duration_sec", "mean"),
        mean_behavior_events=("n_behavior_events", "mean"),
        mean_content=("n_content", "mean"),
        mean_furthest_rank=("furthest_rank", "mean"),
        max_furthest_rank=("furthest_rank", "max"),
        total_behavior_events=("n_behavior_events", "sum"),
        conversion_rate=("converted", "mean"),
        ever_converted=("converted", "max"),
        already_converted_share=("already_converted", "mean"),
        first_session=("session_start", "min"),
        last_session=("session_start", "max"),
        n_devices=("device_type", "nunique"),
        n_referrers=("referrer", "nunique"),
    )

    stage = work.groupby(["anonymous_id", "furthest_stage"], sort=False).size().unstack(fill_value=0)
    for column in ["deep", "intent", "engaged", "landing", "scroll", "none"]:
        if column not in stage.columns:
            stage[column] = 0
    totals = stage.sum(axis=1).replace(0, np.nan)
    features["share_deep"] = (stage["deep"] / totals).fillna(0.0)
    features["share_intent"] = (stage["intent"] / totals).fillna(0.0)
    features["share_engaged"] = (stage["engaged"] / totals).fillna(0.0)
    features["share_landing_or_scroll"] = ((stage["landing"] + stage["scroll"]) / totals).fillna(0.0)

    event_totals = work.groupby("anonymous_id", sort=False)[EVENT_COLUMNS].sum()
    behavior_sum = work.groupby("anonymous_id", sort=False)["n_behavior_events"].sum().replace(0, np.nan)
    for column in EVENT_COLUMNS:
        features[f"{column}_rate"] = (event_totals[column] / behavior_sum).fillna(0.0)
        features[f"total_{column}"] = event_totals[column].astype(np.int64)

    device = work.groupby(["anonymous_id", "device_type"], sort=False).size().unstack(fill_value=0)
    for device_name in ["desktop", "mobile", "tablet"]:
        if device_name not in device.columns:
            device[device_name] = 0
    device_total = device.sum(axis=1).replace(0, np.nan)
    features["share_desktop"] = (device["desktop"] / device_total).fillna(0.0)
    features["share_mobile"] = (device["mobile"] / device_total).fillna(0.0)
    features["share_tablet"] = (device["tablet"] / device_total).fillna(0.0)

    features["days_active"] = (features["last_session"] - features["first_session"]).dt.total_seconds() / 86400.0
    snapshot = features["last_session"].max()
    features["recency_days"] = (snapshot - features["last_session"]).dt.total_seconds() / 86400.0

    hmm_cols = [column for column in work.columns if column.startswith("hmm_share_")]
    if hmm_cols:
        features = features.join(work.groupby("anonymous_id", sort=False)[hmm_cols].mean())

    features = features.reset_index()
    ordered = ["anonymous_id"] + [c for c in USER_FEATURE_COLUMNS if c in features.columns]
    extras = [c for c in features.columns if c not in ordered]
    return features[ordered + extras]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    print("5. Feature Engineering — Session → User-level features")
    sessions = enrich_session_features(load_sessions())
    users = user_features(sessions)

    sessions_path = OUTPUT / "session_features.csv"
    users_path = OUTPUT / "user_features.csv"
    sessions.to_csv(sessions_path, index=False)
    users.to_csv(users_path, index=False)

    print(f"   sessions: {len(sessions):,}")
    print(f"   users (cookies): {len(users):,}")
    print(f"   mean sessions / user: {users['n_sessions'].mean():.2f}")
    print(f"   mean conversion rate: {users['conversion_rate'].mean():.2%}")
    print(f"   users with any deep session: {(users['share_deep'] > 0).mean():.1%}")
    if any(c.startswith("hmm_share_") for c in users.columns):
        print("   HMM mode shares included")
    print("\nTop user feature means")
    preview = [
        "n_sessions",
        "mean_duration_sec",
        "mean_behavior_events",
        "share_deep",
        "subscription_view_rate",
        "checkout_start_rate",
        "conversion_rate",
    ]
    print(users[preview].mean().round(3).to_string())
    print(f"\nwrote {sessions_path}")
    print(f"wrote {users_path}")


if __name__ == "__main__":
    main()
