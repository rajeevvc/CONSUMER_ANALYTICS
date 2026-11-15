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
    print("Goal: measure how deep visits get and where they stall.")
    describe_sessions()
    events = load_toy_events()

    print("\nAlgorithm steps")
    print("  1. Tag each event with a funnel stage")
    print("  2. Mark which stages each session ever touched")
    print("  3. Count sessions at each stage + who ended there")
    print("  4. Advance rate = share that also touched the NEXT stage")
    print("     (co-occurrence — not 'immediate next click')")

    _section("OUTPUT 1 — Input events with stages")
    print(events[["session_idx", "anonymous_id", "timestamp", "event_name", "stage"]].to_string(index=False))
    print("\nPer-session stages touched")
    for sid, part in events.groupby("session_idx", sort=True):
        stages = " → ".join(dict.fromkeys(part["stage"].tolist()))
        print(f"  S{sid}: {stages}")

    table = funnel_table(events)
    _section("OUTPUT 2 — Funnel table")
    print("Column meanings")
    print("  stage                       funnel rung")
    print("  events                      how many events mapped to this stage")
    print("  sessions_containing_stage   visits that ever hit this stage")
    print("  sessions_ending_here        visits whose FURTHEST stage is this one")
    print("  next_stage                  next rung in the ladder")
    print("  advance_rate                share of containing sessions that also hit next_stage")
    print("\nFull table")
    print(table.to_string(index=False))

    _section("OUTPUT 3 — Row-by-row reading")
    for row in table.itertuples(index=False):
        print(f"\n  {row.stage}")
        print(f"    events={row.events}, sessions_with_stage={row.sessions_containing_stage}, "
              f"ended_here={row.sessions_ending_here}")
        if row.next_stage:
            print(f"    next={row.next_stage}, advance_rate={row.advance_rate}")
            if row.stage == "landing":
                print("    interpret: 4 sessions landed; 3 also scrolled → 0.75")
            if row.stage == "intent":
                print("    interpret: 2 sessions reached intent; only 1 also hit deep → 0.50 (cliff)")
        else:
            print("    end of ladder (no next stage)")

    _section("OUTPUT 4 — Acceptance checks")
    landing = table.loc[table["stage"] == "landing"].iloc[0]
    intent = table.loc[table["stage"] == "intent"].iloc[0]
    print(f"  landing advance_rate = {landing.advance_rate}  (expect 0.75)")
    print(f"  intent advance_rate  = {intent.advance_rate}  (expect 0.50)")

    _section("Teaching takeaway")
    print("  Funnel answers: 'How deep did visits get?' and 'Where is the cliff?'")


if __name__ == "__main__":
    main()
