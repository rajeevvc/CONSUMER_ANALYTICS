"""Journey example 1 — Funnel.

Question: How many sessions reached each stage, and how many advanced?

Run:
    python day-1/examples/02_journey/01_funnel_example.py
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
from toy_sessions import FUNNEL_STAGES, describe_sessions, load_toy_events


def funnel_table(events: pd.DataFrame) -> pd.DataFrame:
    """Same idea as step02_journey_analysis.funnel_table (toy-sized)."""
    event_counts = events.groupby("stage", sort=False).size()
    presence = events.groupby(["session_idx", "stage"], sort=False).size().unstack(fill_value=0)
    for stage in FUNNEL_STAGES:
        if stage not in presence.columns:
            presence[stage] = 0
    contains = presence[FUNNEL_STAGES].gt(0)

    rank = {stage: index for index, stage in enumerate(FUNNEL_STAGES)}
    furthest = events["stage"].map(rank).groupby(events["session_idx"], sort=False).max()

    rows = []
    for index, stage in enumerate(FUNNEL_STAGES):
        containing = int(contains[stage].sum())
        next_stage = FUNNEL_STAGES[index + 1] if index + 1 < len(FUNNEL_STAGES) else ""
        advanced = int((contains[stage] & contains[next_stage]).sum()) if next_stage else 0
        rows.append(
            {
                "stage": stage,
                "events": int(event_counts.get(stage, 0)),
                "sessions_containing_stage": containing,
                "sessions_ending_here": int((furthest == index).sum()),
                "next_stage": next_stage or None,
                "advance_rate": round(advanced / containing, 4) if next_stage and containing else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("FUNNEL — reach & advance (stage tags)")
    print("Goal: raw staged events → funnel reach / advance table.")
    describe_sessions()
    events = load_toy_events()

    _section("RAW — input events with stages")
    print(events[["session_idx", "anonymous_id", "timestamp", "event_name", "stage"]].to_string(index=False))

    table = funnel_table(events)
    _section("PROCESSED — funnel table")
    print(table.to_string(index=False))
    print("\nNote: advance_rate = share that also hit the NEXT stage (ever), not next click.")
    print("  landing→scroll = 0.75; intent→deep = 0.50 (cliff).")


if __name__ == "__main__":
    main()
