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


def _explain_event_columns() -> None:
    print("\nColumn meanings (event output)")
    print("  anonymous_id   cookie / visitor ID (long-lived)")
    print("  timestamp      when the event happened")
    print("  event_name     raw click / action")
    print("  gap_seconds    seconds since THIS cookie's previous kept event")
    print("                 NaN = first event for that cookie")
    print("  session_id     visit ID assigned by the 30-minute rule")
    print("  stage          funnel tag for this event (landing…deep / subscription)")
    print("  is_conversion  True only for register_complete / subscription_active")


def _explain_session_columns() -> None:
    print("\nColumn meanings (session summary output)")
    print("  session_id          visit ID")
    print("  anonymous_id        cookie that owned the visit")
    print("  session_start       first event time in the visit")
    print("  duration_sec        first→last BEHAVIOR event span (excludes conversion-only)")
    print("  n_behavior_events   count of non-conversion events in the visit")
    print("  furthest_stage      deepest engagement stage reached in the visit")
    print("  converted           True if cookie's first conversion is within 7 days of start")
    print("  already_converted   True if a conversion already happened before this visit")


def _walk_event_rows(events: pd.DataFrame) -> None:
    print("\nRow-by-row reading of sessionized events")
    for cookie, part in events.groupby("anonymous_id", sort=False):
        print(f"\n  Cookie {cookie}")
        prev_session = None
        for row in part.itertuples(index=False):
            gap = row.gap_seconds
            if pd.isna(gap):
                gap_txt = "NaN (first event for this cookie → always starts a session)"
                decision = "NEW SESSION"
            elif gap > SESSION_GAP_SECONDS:
                gap_txt = f"{gap:.0f}s > {SESSION_GAP_SECONDS}s (30 min) → idle too long"
                decision = "NEW SESSION"
            else:
                gap_txt = f"{gap:.0f}s ≤ {SESSION_GAP_SECONDS}s → still same visit"
                decision = "same session"
            stage_note = f"stage={row.stage}"
            if row.is_conversion:
                stage_note += " | CONVERSION outcome (not browsing depth)"
            print(
                f"    {row.timestamp}  {row.event_name:<20}  "
                f"gap={gap_txt}"
            )
            print(f"      → {decision}: {row.session_id}  ({stage_note})")
            if prev_session is not None and row.session_id != prev_session:
                print(f"      ★ session changed: {prev_session} → {row.session_id}")
            prev_session = row.session_id


def _walk_session_rows(sessions: pd.DataFrame) -> None:
    print("\nRow-by-row reading of session summaries")
    for row in sessions.itertuples(index=False):
        print(f"\n  {row.session_id}  cookie={row.anonymous_id}")
        print(f"    started          {row.session_start}")
        print(f"    duration_sec     {row.duration_sec:.0f}s of active behavior")
        print(f"    n_behavior_events {int(row.n_behavior_events)}")
        print(f"    furthest_stage   {row.furthest_stage} (rank {int(row.furthest_rank)})")
        print(f"    device/referrer  {row.device_type} / {row.referrer}")
        print(f"    converted        {bool(row.converted)}")
        print(f"    already_converted {bool(row.already_converted)}")
        if row.anonymous_id == "A0001" and row.session_id.endswith("0002"):
            print("    note: second visit for A0001 because prior gap was 35 minutes")
        if bool(row.converted):
            print("    note: conversion event occurred in/after this visit within 7 days")


def main() -> None:
    _section("SESSIONIZE — 30-minute inactivity rule")
    print("Goal: turn raw clicks into visits (sessions) + a conversion label.")
    describe_raw()

    print("\nAlgorithm steps")
    print("  1. Sort by cookie + time")
    print("  2. Drop near-duplicates (same cookie/event/content within 2s)")
    print("  3. Tag stage + conversion flags")
    print(f"  4. New session when gap since prior event > {SESSION_GAP_SECONDS}s (30 min)")
    print("  5. Build one session summary row (duration, furthest stage, …)")
    print(f"  6. Label converted if first conversion is within {HORIZON_DAYS} days")

    raw = load_raw_events().sort_values(["anonymous_id", "timestamp"], kind="mergesort")
    _section("OUTPUT 1 — Raw input events")
    print(f"Count: {len(raw)} rows from toy_raw_events.load_raw_events()")
    print(
        raw[["anonymous_id", "timestamp", "event_name", "content_id", "device_type", "referrer"]].to_string(
            index=False
        )
    )
    print("\nLook for: A0001 has two page_view on C001 one second apart (near-duplicate).")

    cleaned = drop_near_duplicates(raw)
    dropped = len(raw) - len(cleaned)
    _section("OUTPUT 2 — After near-duplicate drop")
    print(f"Kept {len(cleaned)} of {len(raw)} events  (dropped {dropped})")
    print("Rule: same cookie + same event_name + same content_id + gap ≤ 2 seconds → drop.")
    if dropped:
        print("Dropped row(s): A0001 page_view at 10:00:01 on C001 (duplicate of 10:00:00).")

    events = sessionize(cleaned)
    _section("OUTPUT 3 — Sessionized event table")
    _explain_event_columns()
    print("\nFull table")
    print(
        events[
            ["anonymous_id", "timestamp", "event_name", "gap_seconds", "session_id", "stage", "is_conversion"]
        ].to_string(index=False)
    )
    _walk_event_rows(events)

    sessions = attach_conversion_label(session_summary(events), events)
    _section("OUTPUT 4 — Session summary table (one row per visit)")
    _explain_session_columns()
    print("\nFull table")
    print(
        sessions[
            [
                "session_id",
                "anonymous_id",
                "session_start",
                "duration_sec",
                "n_behavior_events",
                "furthest_stage",
                "furthest_rank",
                "converted",
                "already_converted",
            ]
        ].to_string(index=False)
    )
    _walk_session_rows(sessions)

    _section("OUTPUT 5 — Acceptance checks")
    a1_sessions = events.loc[events["anonymous_id"] == "A0001", "session_id"].nunique()
    a1_gap = float(
        events.loc[
            (events["anonymous_id"] == "A0001") & (events["timestamp"] == "2026-01-10 10:40:00"),
            "gap_seconds",
        ].iloc[0]
    )
    converters = sessions.loc[sessions["converted"], "session_id"].tolist()
    print(f"  A0001 session count     = {a1_sessions}  (expect 2)")
    print(f"  A0001 10:40 gap_seconds = {a1_gap:.0f}  (expect 2100 > 1800 → new session)")
    print(f"  Events after dedupe     = {len(events)}  (expect 18; raw had 19)")
    print(f"  Converted session_ids   = {converters}  (expect ['S000000005'])")
    print(f"  Total sessions          = {len(sessions)}  (expect 5)")

    _section("Teaching takeaway")
    print("  Cookie (anonymous_id) = long-lived browser identity.")
    print("  Session (session_id)  = one visit; ends after 30 minutes idle.")
    print("  Event table           = every click with its session membership.")
    print("  Session table         = one scorecard per visit for later labs.")
    print("  Next examples         = Journey / HMM / Features / Segmentation.")


if __name__ == "__main__":
    main()
