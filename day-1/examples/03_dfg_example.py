"""Journey example 3 — Directly-Follows Graph (DFG).

Question: What event→event paths actually happen? (process map)

Run:
    python day-1/examples/03_dfg_example.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from toy_sessions import describe_sessions, load_toy_events


def directly_follows(events: pd.DataFrame) -> pd.DataFrame:
    """Build START / event→event / END edges (same idea as step02 DFG)."""
    train = events.sort_values(["session_idx", "timestamp"], kind="mergesort")
    session = train["session_idx"].to_numpy()
    activity = train["event_name"].to_numpy()

    same = session[1:] == session[:-1]
    is_first = np.empty(len(train), dtype=bool)
    is_first[0] = True
    is_first[1:] = session[1:] != session[:-1]
    is_last = np.empty(len(train), dtype=bool)
    is_last[-1] = True
    is_last[:-1] = session[1:] != session[:-1]

    edges = pd.concat(
        [
            pd.DataFrame(
                {
                    "from_activity": "START",
                    "to_activity": activity[is_first],
                    "session_idx": session[is_first],
                }
            ),
            pd.DataFrame(
                {
                    "from_activity": activity[:-1][same],
                    "to_activity": activity[1:][same],
                    "session_idx": session[:-1][same],
                }
            ),
            pd.DataFrame(
                {
                    "from_activity": activity[is_last],
                    "to_activity": "END",
                    "session_idx": session[is_last],
                }
            ),
        ],
        ignore_index=True,
    )
    return edges


def edge_table(edges: pd.DataFrame) -> pd.DataFrame:
    table = edges.groupby(["from_activity", "to_activity"], sort=False).size().reset_index(name="count")
    totals = table.groupby("from_activity")["count"].transform("sum")
    table["probability"] = (table["count"] / totals).round(3)
    return table.sort_values(["count", "from_activity"], ascending=[False, True]).reset_index(drop=True)


def journey_variants(events: pd.DataFrame) -> pd.DataFrame:
    """Collapse consecutive repeats and show each session path."""
    train = events.sort_values(["session_idx", "timestamp"], kind="mergesort")
    session = train["session_idx"].to_numpy()
    name = train["event_name"].to_numpy()
    keep = np.empty(len(train), dtype=bool)
    keep[0] = True
    keep[1:] = (session[1:] != session[:-1]) | (name[1:] != name[:-1])
    collapsed = train.loc[keep, ["session_idx", "event_name"]]
    paths = (
        collapsed.groupby("session_idx")["event_name"]
        .apply(lambda s: " > ".join(s.tolist()) + " > END")
        .rename("journey")
        .reset_index()
    )
    return paths


def main() -> None:
    print("=" * 60)
    print("DFG — event-level process map")
    print("=" * 60)
    describe_sessions()
    events = load_toy_events()

    print("\nWhat the algorithm does")
    print("  1. Use raw EVENT NAMES (not stage tags)")
    print("  2. Add START→first and last→END for every session")
    print("  3. Count every consecutive event pair inside a session")
    print("  4. Optional: list path variants (journeys)")

    print("\nBy-hand check")
    print("  Every session starts with page_view → four START→page_view edges")
    print("  page_view→scroll appears in S2,S3,S4 (not S1)")
    print("  S1 is simply: START → page_view → END")

    edges = directly_follows(events)
    table = edge_table(edges)
    print("\nStrongest follows")
    print(table.head(12).to_string(index=False))

    print("\nJourney variants")
    print(journey_variants(events).to_string(index=False))

    print("\nTeaching takeaway")
    print("  DFG answers: 'What exact click paths happen?'")
    print("  Funnel/Markov use stages; DFG keeps event detail.")


if __name__ == "__main__":
    main()
