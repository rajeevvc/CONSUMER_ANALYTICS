"""Journey example 1 — Funnel.

Question: How many sessions reached each stage, and how many advanced?

Run:
    python day-1/examples/01_funnel_example.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

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


def main() -> None:
    print("=" * 60)
    print("FUNNEL — reach & advance (stage tags)")
    print("=" * 60)
    describe_sessions()
    events = load_toy_events()

    print("\nWhat the algorithm does")
    print("  1. Tag each event with a funnel stage")
    print("  2. Mark which stages each session ever touched")
    print("  3. Count sessions at each stage")
    print("  4. Advance rate = share that also touched the NEXT stage")
    print("     (co-occurrence — not 'immediate next click')")

    print("\nBy-hand check")
    print("  landing in all 4 sessions")
    print("  scroll in S2,S3,S4 → 3/4 = 0.75 advance from landing")
    print("  intent in S3,S4; deep only in S4 → 1/2 = 0.50 intent→deep")

    table = funnel_table(events)
    print("\nFunnel table")
    print(table.to_string(index=False))

    print("\nTeaching takeaway")
    print("  Funnel answers: 'How deep did visits get?' and 'Where is the cliff?'")


if __name__ == "__main__":
    main()
