"""Day 1 — Behavioral State Modeling: HMM (HSMM optional / not required).

Single self-contained script. Run after sessionization:

    python day-1/01_sessionize/step01_sessionize.py
    python day-1/03_state_modeling/step03_behavioral_state_modeling.py

Fits a categorical Hidden Markov Model on clickstream events to recover
latent reading modes (skimming, scrolling, exploring, deep_reading).
Duration is geometric via self-transitions — the usual HMM substitute for
an explicit-duration HSMM.

Writes:

    day-1/output/hmm_modes.csv
    day-1/output/hmm_durations.csv
    day-1/output/hmm_mode_transitions.csv
    day-1/output/hmm_reader_modes.csv
    day-1/output/sessionized_events_hmm.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

DAY1 = Path(__file__).resolve().parents[1]
ROOT = DAY1.parent
OUTPUT = DAY1 / "output"
SESSIONIZED_EVENTS = OUTPUT / "sessionized_events.csv"
if str(DAY1 / "01_sessionize") not in sys.path:
    sys.path.insert(0, str(DAY1 / "01_sessionize"))

# Bundled hmmlearn from the labs package (if not installed in the active env).
VENDOR = ROOT / "marketing-behavioral-labs" / "day1" / ".vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from hmmlearn.hmm import CategoricalHMM

VALID_END = pd.Timestamp("2026-03-01")
STATE_COLUMN = "hmm_state"
MINIMUM_MODE_MASS = 0.30

# Keep in sync with day-1/01_sessionize/step01_sessionize.py event taxonomy.
OBSERVATIONS = [
    "page_view",
    "scroll",
    "engaged_read",
    "share",
    "login",
    "register_start",
    "register_complete",
    "subscription_view",
    "subscribe_click",
    "checkout_start",
    "payment_success",
    "subscription_active",
]
CONVERSION_EVENTS = {"register_complete", "subscription_active"}
MODE_PROFILES: dict[str, tuple[str, ...]] = {
    "skimming": ("page_view", "login"),
    "scrolling": ("scroll",),
    "exploring": ("engaged_read", "share"),
    "deep_reading": (
        "subscription_view",
        "subscribe_click",
        "checkout_start",
        "payment_success",
        "register_start",
    ),
}
REQUIRED_COLUMNS = ("anonymous_id", "timestamp", "event_name", "session_idx")


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_sessionized_events() -> pd.DataFrame:
    """Load step01_sessionize.py CSV; rebuild if missing. Always refresh obs codes."""
    if SESSIONIZED_EVENTS.exists():
        events = pd.read_csv(SESSIONIZED_EVENTS)
    else:
        from step01_sessionize import load_web_events, sessionize

        print("sessionized_events.csv missing — rebuilding sessions")
        events = sessionize(load_web_events())

    missing = [column for column in REQUIRED_COLUMNS if column not in events.columns]
    if missing:
        raise RuntimeError(
            f"{SESSIONIZED_EVENTS.name} missing columns: {', '.join(missing)}. "
            "Re-run python day-1/01_sessionize/step01_sessionize.py."
        )

    unknown = sorted(set(events["event_name"].dropna().astype(str)) - set(OBSERVATIONS))
    if unknown:
        raise RuntimeError(
            f"unknown event_name values: {', '.join(unknown)}. "
            "Update OBSERVATIONS to match the current web taxonomy."
        )

    events = events.copy()
    events["timestamp"] = pd.to_datetime(events["timestamp"])
    events["is_conversion"] = events["event_name"].isin(CONVERSION_EVENTS)
    obs_map = {name: index for index, name in enumerate(OBSERVATIONS)}
    events["obs"] = events["event_name"].map(obs_map).astype("int16")
    return events


# ---------------------------------------------------------------------------
# HMM fit / decode
# ---------------------------------------------------------------------------


def fit_hmm(
    events: pd.DataFrame,
    n_states: int = 4,
    max_sessions: int = 8000,
    max_length: int = 25,
    seed: int = 42,
) -> tuple[CategoricalHMM, dict[int, str]]:
    """Fit a categorical HMM on reading sequences before the March test window."""
    train = events.loc[(events["timestamp"] < VALID_END) & ~events["is_conversion"]]
    session_ids = train["session_idx"].drop_duplicates().to_numpy()
    rng = np.random.default_rng(seed)
    if len(session_ids) > max_sessions:
        session_ids = rng.choice(session_ids, size=max_sessions, replace=False)
    sample = train.loc[train["session_idx"].isin(session_ids), ["session_idx", "timestamp", "obs"]]
    sample = sample.sort_values(["session_idx", "timestamp"], kind="mergesort")
    sample = sample.groupby("session_idx", sort=False).head(max_length)
    lengths = sample.groupby("session_idx", sort=False).size().to_numpy()
    observations = sample["obs"].to_numpy().reshape(-1, 1)
    model = _fit_balanced(observations, lengths, n_states, seed)
    return model, _name_modes(model)


def decode_states(model: CategoricalHMM, events: pd.DataFrame) -> pd.Series:
    """Most likely mode for every reading event. Conversion events stay unassigned."""
    states = np.full(len(events), -1, dtype=np.int16)
    behavior_index = np.flatnonzero(~events["is_conversion"].to_numpy())
    if len(behavior_index) == 0:
        return pd.Series(states, index=events.index, name=STATE_COLUMN)
    behavior = events.iloc[behavior_index]
    order = np.lexsort((behavior["timestamp"].to_numpy(), behavior["session_idx"].to_numpy()))
    ordered = behavior.iloc[order]
    new_session = np.empty(len(ordered), dtype=bool)
    new_session[0] = True
    sessions = ordered["session_idx"].to_numpy()
    new_session[1:] = sessions[1:] != sessions[:-1]
    lengths = np.diff(np.flatnonzero(np.append(new_session, True)))
    decoded = model.predict(ordered["obs"].to_numpy().reshape(-1, 1), lengths)
    restored = np.empty(len(order), dtype=np.int16)
    restored[order] = np.asarray(decoded, dtype=np.int16)
    states[behavior_index] = restored
    return pd.Series(states, index=events.index, name=STATE_COLUMN)


def mode_table(model: CategoricalHMM, names: dict[int, str]) -> pd.DataFrame:
    stay = np.clip(np.diag(model.transmat_), 0.0, 0.999999)
    mean_duration = 1.0 / (1.0 - stay)
    rows = []
    for state, probabilities in enumerate(model.emissionprob_):
        top = int(np.argmax(probabilities))
        rows.append(
            {
                "state": state,
                "mode": names[state],
                "description": _describe(probabilities),
                "start_probability": round(float(model.startprob_[state]), 4),
                "mean_duration_events": round(float(mean_duration[state]), 2),
                "top_event": OBSERVATIONS[top],
                "top_probability": round(float(probabilities[top]), 4),
                **{OBSERVATIONS[index]: round(float(value), 4) for index, value in enumerate(probabilities)},
            }
        )
    return pd.DataFrame(rows)


def duration_table(model: CategoricalHMM, names: dict[int, str], max_duration: int = 10) -> pd.DataFrame:
    """Geometric P(mode lasts d events) — HMM stand-in for HSMM duration distributions."""
    rows = []
    for state, stay in enumerate(np.diag(model.transmat_)):
        stay = float(np.clip(stay, 0.0, 0.999999))
        leave = 1.0 - stay
        for duration in range(1, max_duration + 1):
            probability = (stay ** (duration - 1)) * leave
            rows.append(
                {
                    "mode": names[state],
                    "duration_events": duration,
                    "probability": round(float(probability), 4),
                }
            )
    return pd.DataFrame(rows)


def mode_transitions(model: CategoricalHMM, names: dict[int, str]) -> pd.DataFrame:
    rows = []
    for source, probabilities in enumerate(model.transmat_):
        for target, probability in enumerate(probabilities):
            rows.append(
                {
                    "from_mode": names[source],
                    "to_mode": names[target],
                    "probability": round(float(probability), 4),
                    "is_self": source == target,
                }
            )
    return pd.DataFrame(rows)


def reader_mode_summary(events: pd.DataFrame, names: dict[int, str]) -> pd.DataFrame:
    work = events.loc[events[STATE_COLUMN] >= 0, ["anonymous_id", STATE_COLUMN]]
    counts = work.groupby(["anonymous_id", STATE_COLUMN], sort=False).size().unstack(fill_value=0)
    counts.columns = counts.columns.astype(int)
    for state in names:
        if state not in counts.columns:
            counts[state] = 0
    counts = counts[list(names)]
    shares = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    dominant = np.array([names[list(names)[index]] for index in shares.to_numpy().argmax(axis=1)])
    event_counts = {int(state): int(count) for state, count in work[STATE_COLUMN].value_counts().items()}
    total_events = sum(event_counts.values()) or 1
    rows = []
    for state, mode in names.items():
        selected = dominant == mode
        rows.append(
            {
                "mode": mode,
                "dominant_readers": int(selected.sum()),
                "share_of_readers": round(float(selected.mean()) if len(selected) else 0.0, 4),
                "mean_share_of_events": round(float(shares[state].mean()), 4),
                "event_share": round(event_counts.get(state, 0) / total_events, 4),
            }
        )
    return pd.DataFrame(rows).sort_values(["event_share", "dominant_readers"], ascending=False).reset_index(drop=True)


def _fit_balanced(
    observations: np.ndarray,
    lengths: np.ndarray,
    n_states: int,
    seed: int,
    restarts: int = 6,
) -> CategoricalHMM:
    best_model = None
    best_key = None
    for restart in range(restarts):
        model = CategoricalHMM(
            n_components=n_states,
            n_features=len(OBSERVATIONS),
            n_iter=40,
            tol=1e-3,
            random_state=seed + restart,
            verbose=False,
        )
        model.fit(observations, lengths)
        occupied = np.bincount(model.predict(observations, lengths), minlength=n_states) / len(observations)
        score = float(model.score(observations, lengths))
        key = (float(occupied.min()), score)
        if best_key is None or key > best_key:
            best_key = key
            best_model = model
    if best_model is None:
        raise RuntimeError("HMM fit did not produce a model")
    return best_model


def _name_modes(model: CategoricalHMM) -> dict[int, str]:
    profiles = list(MODE_PROFILES)
    profile_index = [[OBSERVATIONS.index(event) for event in MODE_PROFILES[profile]] for profile in profiles]
    mass = np.array(
        [
            [float(model.emissionprob_[state, indexes].sum()) for indexes in profile_index]
            for state in range(model.n_components)
        ]
    )
    names: dict[int, str] = {}
    used: set[str] = set()
    order = sorted(
        (
            (mass[state, profile], state, profile)
            for state in range(model.n_components)
            for profile in range(len(profiles))
        ),
        reverse=True,
    )
    for score, state, profile in order:
        mode = profiles[profile]
        if state in names or mode in used or score < MINIMUM_MODE_MASS:
            continue
        names[state] = mode
        used.add(mode)
    leftovers = [state for state in range(model.n_components) if state not in names]
    page_view = OBSERVATIONS.index("page_view")
    leftovers.sort(key=lambda state: float(model.emissionprob_[state, page_view]), reverse=True)
    fallback = ["light_reading", "broad_reading", "mixed_reading"]
    for index, state in enumerate(leftovers):
        names[state] = fallback[index] if index < len(fallback) else f"mixed_reading_{index + 1}"
    return names


def _describe(probabilities: np.ndarray) -> str:
    parts = []
    for index in np.argsort(-probabilities):
        if probabilities[index] < 0.05 or OBSERVATIONS[index] in CONVERSION_EVENTS:
            continue
        parts.append(f"{OBSERVATIONS[index]} {probabilities[index]:.0%}")
        if len(parts) == 3:
            break
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    events = load_sessionized_events()

    print("4. Behavioral State Modeling — HMM (HSMM optional)")
    print(f"   events: {len(events):,}  sessions: {events['session_idx'].nunique():,}")

    model, names = fit_hmm(events)
    events[STATE_COLUMN] = decode_states(model, events)
    events["hmm_mode"] = events[STATE_COLUMN].map(lambda s: names.get(int(s), "") if s >= 0 else "")

    modes = mode_table(model, names)
    durations = duration_table(model, names)
    transitions = mode_transitions(model, names)
    readers = reader_mode_summary(events, names)
    overview = readers.merge(
        modes[["mode", "description", "start_probability", "mean_duration_events"]],
        on="mode",
        how="left",
    )

    modes.to_csv(OUTPUT / "hmm_modes.csv", index=False)
    durations.to_csv(OUTPUT / "hmm_durations.csv", index=False)
    transitions.to_csv(OUTPUT / "hmm_mode_transitions.csv", index=False)
    overview.to_csv(OUTPUT / "hmm_reader_modes.csv", index=False)
    events.to_csv(OUTPUT / "sessionized_events_hmm.csv", index=False)

    print("\nLatent modes")
    for row in overview.itertuples(index=False):
        role = (
            f"dominant for {row.share_of_readers:.0%} of readers"
            if row.share_of_readers >= 0.01
            else "usually a secondary mode"
        )
        share = row.mean_share_of_events
        share_text = f"{share:.0%} of a reader's events" if share >= 0.01 else "rare"
        print(
            f"  {row.mode}: {share_text}, "
            f"mean sojourn {row.mean_duration_events:.1f} events, {role} — {row.description}"
        )

    print(f"\nwrote files under {OUTPUT}")


if __name__ == "__main__":
    main()
