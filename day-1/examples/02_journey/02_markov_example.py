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
    print("Goal: raw stage sequences → P(next stage | current), including exit.")
    describe_sessions()
    events = load_toy_events()

    _section("RAW — stage sequence per session")
    for sid, part in events.sort_values(["session_idx", "timestamp"]).groupby("session_idx", sort=True):
        print(f"  S{sid}: {' → '.join(part['stage'].tolist())} → exit")

    matrix, _dropoff = fit_markov(events)
    _section("PROCESSED — transition matrix")
    print(matrix.to_string())
    print("\nNote: each row ≈ P(next | current), including exit. "
          "landing→scroll=0.75, landing→exit=0.25.")


if __name__ == "__main__":
    main()
