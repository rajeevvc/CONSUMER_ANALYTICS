"""Journey example 2 — First-order Markov chain (stages + exit).

Question: Given the current stage, where do people go next — or exit?

Run:
    python day-1/examples/02_journey/02_markov_example.py
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

MARKOV_STATES = FUNNEL_STAGES + ["exit"]


def fit_markov(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Same idea as step02_journey_analysis.fit_markov (toy-sized)."""
    train = events.sort_values(["session_idx", "timestamp"], kind="mergesort")
    stage = train["stage"].map({name: i for i, name in enumerate(MARKOV_STATES)}).to_numpy()
    session = train["session_idx"].to_numpy()

    counts = np.zeros((len(MARKOV_STATES), len(MARKOV_STATES)), dtype=np.int64)
    same = session[1:] == session[:-1]
    np.add.at(counts, (stage[:-1][same], stage[1:][same]), 1)

    is_last = np.empty(len(session), dtype=bool)
    is_last[-1] = True
    is_last[:-1] = session[1:] != session[:-1]
    exit_i = MARKOV_STATES.index("exit")
    np.add.at(counts, (stage[is_last], np.full(int(is_last.sum()), exit_i)), 1)

    totals = counts.sum(axis=1, keepdims=True)
    probs = np.divide(counts, totals, out=np.zeros_like(counts, dtype=float), where=totals > 0)

    matrix = pd.DataFrame(probs, index=MARKOV_STATES, columns=MARKOV_STATES).loc[
        FUNNEL_STAGES, MARKOV_STATES
    ]
    dropoff = pd.DataFrame(
        [
            {
                "stage": stage_name,
                "transitions": int(counts[i].sum()),
                "exits": int(counts[i, exit_i]),
                "exit_probability": round(float(probs[i, exit_i]), 4),
            }
            for i, stage_name in enumerate(FUNNEL_STAGES)
        ]
    )
    return matrix.round(3), dropoff


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("MARKOV — next-stage probabilities (+ exit)")
    print("Goal: estimate P(next stage | current stage), including leaving the visit.")
    describe_sessions()
    events = load_toy_events()

    print("\nAlgorithm steps")
    print("  1. Walk each session in time order as a sequence of STAGES")
    print("  2. Count consecutive pairs: landing→scroll, scroll→engaged, …")
    print("  3. After the LAST event of a session, add stage→exit")
    print("  4. Row-normalize counts → P(next | current)")

    _section("OUTPUT 1 — Stage sequence per session")
    for sid, part in events.sort_values(["session_idx", "timestamp"]).groupby("session_idx", sort=True):
        seq = " → ".join(part["stage"].tolist()) + " → exit"
        print(f"  S{sid}: {seq}")
    print("\nSession endings → exit edges")
    print("  S1 ends on landing       → landing→exit")
    print("  S2 ends on engaged       → engaged→exit")
    print("  S3 ends on intent        → intent→exit")
    print("  S4 ends on subscription  → subscription→exit")

    matrix, dropoff = fit_markov(events)
    _section("OUTPUT 2 — Transition matrix")
    print("How to read: each ROW is the current stage; cells are P(go to column | row).")
    print("Rows roughly sum to 1.0 (including exit).")
    print("\nFull matrix")
    print(matrix.to_string())
    print("\nHighlighted cells")
    print(f"  P(scroll | landing) = {matrix.loc['landing', 'scroll']}  (3 of 4 landing steps go to scroll)")
    print(f"  P(exit | landing)   = {matrix.loc['landing', 'exit']}  (S1 bounces)")
    print(f"  P(deep | intent)    = {matrix.loc['intent', 'deep']}  (intent rarely becomes checkout)")

    _section("OUTPUT 3 — Drop-off table")
    print("Column meanings")
    print("  stage             current stage")
    print("  transitions       outbound counts from this stage (incl. exit)")
    print("  exits             how often the visit ended here")
    print("  exit_probability  P(exit | stage)")
    print("\nFull table")
    print(dropoff.to_string(index=False))
    print("\nRow-by-row")
    for row in dropoff.itertuples(index=False):
        if row.transitions == 0:
            continue
        print(f"  {row.stage}: {row.exits}/{row.transitions} exits → P(exit)={row.exit_probability}")

    _section("OUTPUT 4 — Acceptance checks")
    print(f"  landing→scroll = {matrix.loc['landing', 'scroll']}  (expect 0.75)")
    print(f"  landing→exit   = {matrix.loc['landing', 'exit']}  (expect 0.25)")
    print(f"  engaged→exit   = {matrix.loc['engaged', 'exit']}  (expect ~0.333)")

    _section("Teaching takeaway")
    print("  Markov answers: 'Right after this stage, what usually happens next?'")
    print("  Different from Funnel (Funnel = ever reached; Markov = next step).")


if __name__ == "__main__":
    main()
