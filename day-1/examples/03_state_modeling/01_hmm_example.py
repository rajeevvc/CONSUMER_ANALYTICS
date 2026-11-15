"""State-modeling example — Categorical HMM (latent reading modes).

Question: What hidden mode is active behind each click?

Run:
    python day-1/examples/03_state_modeling/01_hmm_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_DAY1 = Path(__file__).resolve().parents[2]
_ROOT = _DAY1.parent
VENDOR = _ROOT / "marketing-behavioral-labs" / "day1" / ".vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from hmmlearn.hmm import CategoricalHMM

_EXAMPLES = Path(__file__).resolve().parents[1]
_SHARED = _EXAMPLES / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
from toy_sessions import describe_sessions, load_toy_events

# Small vocabulary for a clear 2-mode demo (lab uses 12 events / 4 modes).
OBS = [
    "page_view",
    "scroll",
    "engaged_read",
    "subscription_view",
    "subscribe_click",
    "checkout_start",
    "payment_success",
]
CONVERSION = {"subscription_active", "register_complete"}


def encode(events: pd.DataFrame) -> pd.DataFrame:
    work = events.loc[~events["event_name"].isin(CONVERSION)].copy()
    work["obs"] = work["event_name"].map({name: i for i, name in enumerate(OBS)})
    work = work.dropna(subset=["obs"]).copy()
    work["obs"] = work["obs"].astype(int)
    return work


def fit_and_decode(events: pd.DataFrame) -> tuple[CategoricalHMM, pd.DataFrame, dict[int, str]]:
    """Fit a 2-state categorical HMM and Viterbi-decode each event."""
    work = encode(events).sort_values(["session_idx", "timestamp"])
    lengths = work.groupby("session_idx", sort=False).size().to_numpy()
    X = work["obs"].to_numpy().reshape(-1, 1)

    model = CategoricalHMM(
        n_components=2,
        n_features=len(OBS),
        n_iter=50,
        tol=1e-3,
        random_state=42,
        verbose=False,
    )
    model.fit(X, lengths)
    work = work.copy()
    work["hmm_state"] = model.predict(X, lengths)

    # Name modes from emission mass (skimming vs exploring).
    emissions = model.emissionprob_
    skim_mass = emissions[:, OBS.index("page_view")] + emissions[:, OBS.index("scroll")]
    names = {0: "mode_A", 1: "mode_B"}
    if skim_mass[0] >= skim_mass[1]:
        names = {0: "skimming_like", 1: "exploring_like"}
    else:
        names = {0: "exploring_like", 1: "skimming_like"}
    work["hmm_mode"] = work["hmm_state"].map(names)
    return model, work, names


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("HMM — latent reading modes (toy 2-state demo)")
    print("Goal: learn hidden modes that explain event sequences.")
    describe_sessions()
    events = load_toy_events()

    print("\nAlgorithm steps")
    print("  1. Encode event_name → integer observation codes")
    print("  2. Drop conversion outcomes (not browsing behavior)")
    print("  3. Initialize start/transition/emission randomly (seeded)")
    print("  4. EM (Baum–Welch) learns P(event|mode) and P(mode→mode)")
    print("  5. Viterbi assigns the most likely mode to each event")
    print("\nLab note: Day 1 uses 4 modes + 12 events + 6 random restarts.")
    print("  This example uses 2 modes so the toy data stays readable.")

    _section("OUTPUT 1 — Observation alphabet")
    print("  Codes used for CategoricalHMM:")
    for i, name in enumerate(OBS):
        print(f"    {i} = {name}")
    print("\nEvents kept for training (conversion outcomes dropped)")
    work = events.loc[~events["event_name"].isin(CONVERSION)].copy()
    print(work[["session_idx", "event_name", "stage"]].to_string(index=False))

    model, decoded, names = fit_and_decode(events)

    _section("OUTPUT 2 — Learned emissions P(event | mode)")
    print("How to read: each ROW is a mode; cells are P(emit that event | mode).")
    print("Mode labels come from which mode puts more mass on page_view+scroll.")
    emit = pd.DataFrame(model.emissionprob_, columns=OBS)
    emit.insert(0, "mode", [names[i] for i in range(model.n_components)])
    print("\nFull emission table")
    print(emit.round(3).to_string(index=False))
    print("\nMode naming")
    for i in range(model.n_components):
        skim = float(model.emissionprob_[i, OBS.index("page_view")] + model.emissionprob_[i, OBS.index("scroll")])
        print(f"  state {i} → {names[i]}  (page_view+scroll mass={skim:.3f})")

    _section("OUTPUT 3 — Transition matrix P(next mode | current)")
    trans = pd.DataFrame(
        model.transmat_,
        index=[names[i] for i in range(2)],
        columns=[names[i] for i in range(2)],
    )
    print("Rows sum ≈ 1.0. High diagonal = mode persistence.")
    print(trans.round(3).to_string())
    print("\nStart probabilities π")
    for i, p in enumerate(model.startprob_):
        print(f"  P(start in {names[i]}) = {p:.3f}")

    _section("OUTPUT 4 — Decoded events (Viterbi)")
    print("Column meanings")
    print("  session_idx  visit id")
    print("  event_name   observation")
    print("  hmm_mode     most likely latent mode at that step")
    print("\nFull decode")
    print(decoded[["session_idx", "event_name", "hmm_mode"]].to_string(index=False))
    print("\nPer-session mode path")
    for sid, part in decoded.groupby("session_idx", sort=True):
        path = " → ".join(part["hmm_mode"].tolist())
        print(f"  S{sid}: {path}")

    _section("OUTPUT 5 — Acceptance checks")
    print(f"  n_components = {model.n_components}  (expect 2)")
    print(f"  decoded rows = {len(decoded)}  (expect {len(work)})")
    print(f"  modes named  = {sorted(set(names.values()))}")

    _section("Teaching takeaway")
    print("  HMM answers: 'What reading mode is happening inside the visit?'")
    print("  Different from Funnel/Markov stages (rules) — modes are learned.")


if __name__ == "__main__":
    main()
