"""Journey example 3 — Directly-Follows Graph (DFG).

Question: What event→event paths actually happen? (process map)

Run:
    python day-1/examples/02_journey/03_dfg_example.py
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


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("DFG — event-level process map")
    print("Goal: show the real click-to-click graph (not stage tags).")
    describe_sessions()
    events = load_toy_events()

    print("\nAlgorithm steps")
    print("  1. Use raw EVENT NAMES (not stage tags)")
    print("  2. Add START→first and last→END for every session")
    print("  3. Count every consecutive event pair inside a session")
    print("  4. List path variants (journeys)")

    _section("OUTPUT 1 — Input event names by session")
    for sid, part in events.sort_values(["session_idx", "timestamp"]).groupby("session_idx", sort=True):
        print(f"  S{sid}: {' > '.join(part['event_name'].tolist())}")

    edges = directly_follows(events)
    _section("OUTPUT 2 — Directly-follows edges (raw pairs)")
    print("Each row is one observed edge instance (before aggregation).")
    print(edges.to_string(index=False))
    print(f"\nTotal edge instances: {len(edges)} "
          f"(4 START + internal follows + 4 END)")

    table = edge_table(edges)
    _section("OUTPUT 3 — Aggregated edge table")
    print("Column meanings")
    print("  from_activity / to_activity  event pair (or START/END)")
    print("  count                        how many times this pair occurred")
    print("  probability                  share among outbound edges from from_activity")
    print("\nFull table (sorted by count)")
    print(table.to_string(index=False))
    print("\nHighlighted edges")
    start_pv = table.loc[table["from_activity"].eq("START") & table["to_activity"].eq("page_view")].iloc[0]
    print(f"  START→page_view count={start_pv['count']} P={start_pv['probability']}  (every session starts here)")
    pv_scroll = table.loc[table["from_activity"].eq("page_view") & table["to_activity"].eq("scroll")]
    if len(pv_scroll):
        row = pv_scroll.iloc[0]
        print(f"  page_view→scroll count={row['count']} P={row['probability']}  (S2,S3,S4; not bounce S1)")

    variants = journey_variants(events)
    _section("OUTPUT 4 — Journey variants")
    print("One collapsed path per session (consecutive repeats would merge if present).")
    print(variants.to_string(index=False))
    print("\nRow-by-row")
    for row in variants.itertuples(index=False):
        print(f"  S{row.session_idx}: {row.journey}")

    _section("OUTPUT 5 — Acceptance checks")
    print(f"  START→page_view count = {int(start_pv['count'])}  (expect 4)")
    print(f"  journey variants      = {len(variants)}  (expect 4)")

    _section("Teaching takeaway")
    print("  DFG answers: 'What exact click paths happen?'")
    print("  Funnel/Markov use stages; DFG keeps event detail.")


if __name__ == "__main__":
    main()
