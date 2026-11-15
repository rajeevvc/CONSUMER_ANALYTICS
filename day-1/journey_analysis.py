"""Day 1 — Journey Analysis: DFG + Funnel + Markov Chain.

Single self-contained script. Run after sessionization:

    python day-1/sessionize.py
    python day-1/journey_analysis.py

Uses day-1/output/sessionized_events.csv when present; otherwise rebuilds
sessions from day-1/data. Writes:

    day-1/output/funnel.csv
    day-1/output/markov_transitions.csv
    day-1/output/markov_transition_matrix.csv
    day-1/output/markov_dropoff.csv
    day-1/output/dfg_activities.csv
    day-1/output/dfg_edges.csv
    day-1/output/dfg_loops.csv
    day-1/output/dfg_journeys.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
SESSIONIZED_EVENTS = OUTPUT / "sessionized_events.csv"

VALID_END = pd.Timestamp("2026-03-01")
MAX_VARIANT_STEPS = 6

# Keep in sync with day-1/sessionize.py (new web event taxonomy).
CONVERSION_EVENTS = {"register_complete", "subscription_active"}
STAGE_BY_EVENT = {
    "page_view": "landing",
    "login": "landing",
    "scroll": "scroll",
    "engaged_read": "engaged",
    "share": "intent",
    "subscription_view": "intent",
    "subscribe_click": "intent",
    "checkout_start": "deep",
    "payment_success": "deep",
    "register_start": "registration",
    "register_complete": "registration",
    "subscription_active": "subscription",
}
FUNNEL_STAGES = ["landing", "scroll", "engaged", "intent", "deep", "registration", "subscription"]
MARKOV_STATES = FUNNEL_STAGES + ["exit"]
INTERVENING_STAGES = ["landing", "scroll", "engaged", "intent", "deep"]


# ---------------------------------------------------------------------------
# Load sessionized clickstream
# ---------------------------------------------------------------------------


def load_sessionized_events() -> pd.DataFrame:
    """Load sessionize.py CSV output; rebuild if missing."""
    if SESSIONIZED_EVENTS.exists():
        events = pd.read_csv(SESSIONIZED_EVENTS)
    else:
        from sessionize import load_web_events, sessionize

        print("sessionized_events.csv missing — rebuilding sessions")
        events = sessionize(load_web_events())

    required = {"anonymous_id", "timestamp", "event_name", "session_idx"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"{SESSIONIZED_EVENTS.name} missing columns: {', '.join(missing)}")

    events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce")
    events = events.dropna(subset=["anonymous_id", "timestamp", "event_name", "session_idx"]).copy()
    events["session_idx"] = events["session_idx"].astype(np.int64)
    events["event_name"] = events["event_name"].astype(str)
    events["stage"] = events["event_name"].map(STAGE_BY_EVENT).fillna("landing")
    events["is_conversion"] = events["event_name"].isin(CONVERSION_EVENTS)
    return events.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Funnel
# ---------------------------------------------------------------------------


def funnel_table(events: pd.DataFrame) -> pd.DataFrame:
    """Sessions containing each stage, and advance rate to the next stage."""
    event_counts = events.groupby("stage", sort=False).size()
    presence = events.groupby(["session_idx", "stage"], sort=False).size().unstack(fill_value=0)
    for stage in FUNNEL_STAGES:
        if stage not in presence.columns:
            presence[stage] = 0
    contains = presence[FUNNEL_STAGES].gt(0)
    stage_rank = events["stage"].map({stage: index for index, stage in enumerate(FUNNEL_STAGES)})
    furthest = stage_rank.groupby(events["session_idx"], sort=False).max()

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
                "next_stage": next_stage,
                "sessions_also_containing_next_stage": advanced if next_stage else np.nan,
                "advance_rate": round(advanced / containing, 4) if next_stage and containing else np.nan,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Markov chain (funnel stages + exit)
# ---------------------------------------------------------------------------


def fit_markov(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """First-order stage transitions on sessions before the March test window."""
    train = events.loc[events["timestamp"] < VALID_END].sort_values(
        ["session_idx", "timestamp"], kind="mergesort"
    )
    stage = train["stage"].map({name: index for index, name in enumerate(MARKOV_STATES)}).to_numpy()
    session = train["session_idx"].to_numpy()
    same_session = session[1:] == session[:-1]
    counts = np.zeros((len(MARKOV_STATES), len(MARKOV_STATES)), dtype=np.int64)
    np.add.at(counts, (stage[:-1][same_session], stage[1:][same_session]), 1)

    is_last = np.empty(len(session), dtype=bool)
    is_last[-1] = True
    is_last[:-1] = session[1:] != session[:-1]
    exit_index = MARKOV_STATES.index("exit")
    np.add.at(counts, (stage[is_last], np.full(int(is_last.sum()), exit_index)), 1)

    totals = counts.sum(axis=1, keepdims=True)
    probabilities = np.divide(counts, totals, out=np.zeros(counts.shape, dtype=float), where=totals > 0)
    transitions = _markov_long(counts, probabilities)
    dropoff = _markov_dropoff(counts, probabilities)
    matrix = (
        transitions.pivot(index="from_stage", columns="to_stage", values="probability")
        .reindex(index=FUNNEL_STAGES, columns=MARKOV_STATES)
        .fillna(0.0)
        .round(6)
    )
    eligible = dropoff.loc[dropoff["stage"].isin(INTERVENING_STAGES) & dropoff["transitions"].ge(1000)]
    biggest = str(eligible.sort_values("exit_probability", ascending=False).iloc[0]["stage"])
    return transitions, dropoff, matrix, biggest


def _markov_long(counts: np.ndarray, probabilities: np.ndarray) -> pd.DataFrame:
    rows = []
    for source, source_name in enumerate(MARKOV_STATES):
        if source_name == "exit":
            continue
        for target, target_name in enumerate(MARKOV_STATES):
            if counts[source, target] == 0:
                continue
            rows.append(
                {
                    "from_stage": source_name,
                    "to_stage": target_name,
                    "count": int(counts[source, target]),
                    "probability": round(float(probabilities[source, target]), 6),
                }
            )
    return pd.DataFrame(rows)


def _markov_dropoff(counts: np.ndarray, probabilities: np.ndarray) -> pd.DataFrame:
    exit_index = MARKOV_STATES.index("exit")
    rows = []
    for index, stage in enumerate(FUNNEL_STAGES):
        total = int(counts[index].sum())
        rows.append(
            {
                "stage": stage,
                "transitions": total,
                "exits": int(counts[index, exit_index]),
                "exit_probability": round(float(probabilities[index, exit_index]), 6),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Directly-follows graph (event-level process map)
# ---------------------------------------------------------------------------


def fit_dfg(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Observed event-to-event graph on sessions before March."""
    train = events.loc[events["timestamp"] < VALID_END].sort_values(
        ["session_idx", "timestamp"], kind="mergesort"
    )
    pairs = _directly_follows(train)
    edges = _edge_table(pairs)
    activities = _activity_table(train, pairs)
    loops = _loops(train, edges)
    journeys = _variants(train)
    return {
        "activities": activities,
        "edges": edges,
        "loops": loops,
        "journeys": journeys,
    }


def _directly_follows(train: pd.DataFrame) -> pd.DataFrame:
    session = train["session_idx"].to_numpy()
    activity = train["event_name"].to_numpy()
    same = session[1:] == session[:-1]
    is_first = np.empty(len(train), dtype=bool)
    is_first[0] = True
    is_first[1:] = session[1:] != session[:-1]
    is_last = np.empty(len(train), dtype=bool)
    is_last[-1] = True
    is_last[:-1] = session[1:] != session[:-1]
    internal = pd.DataFrame(
        {
            "session_idx": session[:-1][same],
            "from_activity": activity[:-1][same],
            "to_activity": activity[1:][same],
        }
    )
    starts = pd.DataFrame(
        {
            "session_idx": session[is_first],
            "from_activity": "START",
            "to_activity": activity[is_first],
        }
    )
    ends = pd.DataFrame(
        {
            "session_idx": session[is_last],
            "from_activity": activity[is_last],
            "to_activity": "END",
        }
    )
    return pd.concat([starts, internal, ends], ignore_index=True)


def _edge_table(pairs: pd.DataFrame) -> pd.DataFrame:
    edges = pairs.groupby(["from_activity", "to_activity"], sort=False).size().reset_index(name="count")
    cases = (
        pairs.drop_duplicates(["session_idx", "from_activity", "to_activity"])
        .groupby(["from_activity", "to_activity"], sort=False)
        .size()
        .rename("case_count")
    )
    edges = edges.join(cases, on=["from_activity", "to_activity"])
    totals = edges.groupby("from_activity")["count"].transform("sum")
    edges["probability"] = (edges["count"] / totals).round(6)
    reverse = edges.set_index(["to_activity", "from_activity"])["count"]
    backward = np.asarray(
        [
            0 if source == target else int(reverse.get((source, target), 0))
            for source, target in zip(edges["from_activity"], edges["to_activity"])
        ]
    )
    forward = edges["count"].to_numpy()
    self_loop = edges["from_activity"].eq(edges["to_activity"]).to_numpy()
    dependency = np.empty(len(edges), dtype=float)
    dependency[self_loop] = forward[self_loop] / (forward[self_loop] + 1)
    other = ~self_loop
    dependency[other] = (forward[other] - backward[other]) / (forward[other] + backward[other] + 1)
    edges["dependency"] = np.round(dependency, 4)
    edges["is_self_loop"] = self_loop
    edges["is_start"] = edges["from_activity"].eq("START")
    edges["is_end"] = edges["to_activity"].eq("END")
    return edges.sort_values(["count", "from_activity"], ascending=[False, True]).reset_index(drop=True)


def _activity_table(train: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    events = train.groupby("event_name", sort=False).size().rename("events")
    sessions = train.groupby("event_name", sort=False)["session_idx"].nunique().rename("sessions")
    starts = (
        pairs.loc[pairs["from_activity"].eq("START")]
        .groupby("to_activity", sort=False)
        .size()
        .rename("start_sessions")
    )
    ends = (
        pairs.loc[pairs["to_activity"].eq("END")]
        .groupby("from_activity", sort=False)
        .size()
        .rename("end_sessions")
    )
    table = pd.concat([events, sessions], axis=1)
    table = table.join(starts, how="left").join(ends, how="left").fillna(0)
    table[["sessions", "start_sessions", "end_sessions"]] = table[
        ["sessions", "start_sessions", "end_sessions"]
    ].astype(np.int64)
    table = table.reset_index(names="activity")
    n_traces = int(pairs.loc[pairs["from_activity"].eq("START"), "session_idx"].nunique()) or 1
    table["start_share"] = (table["start_sessions"] / n_traces).round(4)
    table["end_share"] = (table["end_sessions"] / n_traces).round(4)
    return table.sort_values("events", ascending=False).reset_index(drop=True)


def _loops(train: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    self_loops = edges.loc[
        edges["is_self_loop"],
        ["from_activity", "to_activity", "count", "case_count", "probability", "dependency"],
    ].copy()
    self_loops.insert(0, "loop_type", "self_loop")
    self_loops["loop"] = self_loops["from_activity"] + " > " + self_loops["to_activity"]

    session = train["session_idx"].to_numpy()
    activity = train["event_name"].to_numpy()
    if len(train) < 3:
        cycles = pd.DataFrame(
            columns=[
                "loop_type",
                "loop",
                "from_activity",
                "to_activity",
                "count",
                "case_count",
                "probability",
                "dependency",
            ]
        )
    else:
        same = (session[:-2] == session[1:-1]) & (session[1:-1] == session[2:])
        returned = same & (activity[:-2] == activity[2:]) & (activity[:-2] != activity[1:-1])
        observed = pd.DataFrame(
            {
                "session_idx": session[:-2][returned],
                "from_activity": activity[:-2][returned],
                "via_activity": activity[1:-1][returned],
            }
        )
        cycles = observed.groupby(["from_activity", "via_activity"], sort=False).size().reset_index(name="count")
        case_count = (
            observed.drop_duplicates(["session_idx", "from_activity", "via_activity"])
            .groupby(["from_activity", "via_activity"], sort=False)
            .size()
            .rename("case_count")
        )
        cycles = cycles.join(case_count, on=["from_activity", "via_activity"])
        cycles["loop_type"] = "return_loop"
        cycles["loop"] = cycles["from_activity"] + " > " + cycles["via_activity"] + " > " + cycles["from_activity"]
        cycles["to_activity"] = cycles["from_activity"]
        n_windows = int(same.sum()) or 1
        cycles["probability"] = (cycles["count"] / n_windows).round(6)
        cycles["dependency"] = np.nan
        cycles = cycles[
            [
                "loop_type",
                "loop",
                "from_activity",
                "to_activity",
                "count",
                "case_count",
                "probability",
                "dependency",
            ]
        ]
    self_loops = self_loops[
        [
            "loop_type",
            "loop",
            "from_activity",
            "to_activity",
            "count",
            "case_count",
            "probability",
            "dependency",
        ]
    ]
    loops = pd.concat([self_loops, cycles], ignore_index=True)
    return loops.sort_values("count", ascending=False).reset_index(drop=True)


def _variants(train: pd.DataFrame) -> pd.DataFrame:
    """Most common collapsed event paths. Repeated events in a row count once."""
    session = train["session_idx"].to_numpy()
    name = train["event_name"].to_numpy()
    keep = np.empty(len(train), dtype=bool)
    keep[0] = True
    keep[1:] = (session[1:] != session[:-1]) | (name[1:] != name[:-1])
    collapsed = train.loc[keep, ["session_idx", "event_name"]].copy()
    collapsed["step"] = collapsed.groupby("session_idx", sort=False).cumcount()
    head = collapsed.loc[collapsed["step"] < MAX_VARIANT_STEPS]
    wide = head.pivot(index="session_idx", columns="step", values="event_name")
    path = pd.Series("", index=wide.index, dtype="object")
    for step in wide.columns:
        piece = wide[step]
        path = path.mask(piece.notna() & path.eq(""), piece)
        path = path.mask(piece.notna() & path.ne("") & ~path.eq(piece), path + " > " + piece.fillna(""))
    path = path.mask(path.ne("") & ~path.str.endswith("END"), path + " > END")
    summary = path.value_counts().rename_axis("journey").reset_index(name="sessions")
    summary["share_of_sessions"] = (summary["sessions"] / len(path)).round(4)
    return summary.head(20).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    events = load_sessionized_events()

    print("3. Journey Analysis — DFG + Funnel + Markov Chain")
    print(f"   events: {len(events):,}  sessions: {events['session_idx'].nunique():,}")

    funnel = funnel_table(events)
    funnel.to_csv(OUTPUT / "funnel.csv", index=False)
    print("\nFunnel")
    print(funnel.to_string(index=False))

    transitions, dropoff, matrix, biggest = fit_markov(events)
    transitions.to_csv(OUTPUT / "markov_transitions.csv", index=False)
    matrix.to_csv(OUTPUT / "markov_transition_matrix.csv")
    dropoff.to_csv(OUTPUT / "markov_dropoff.csv", index=False)
    print("\nMarkov transition matrix")
    print(matrix.to_string())
    print(f"highest exit probability before registration: {biggest}")

    dfg = fit_dfg(events)
    dfg["activities"].to_csv(OUTPUT / "dfg_activities.csv", index=False)
    dfg["edges"].to_csv(OUTPUT / "dfg_edges.csv", index=False)
    dfg["loops"].to_csv(OUTPUT / "dfg_loops.csv", index=False)
    dfg["journeys"].to_csv(OUTPUT / "dfg_journeys.csv", index=False)
    top_edges = dfg["edges"].loc[
        ~dfg["edges"]["from_activity"].eq("START")
        & ~dfg["edges"]["to_activity"].eq("END")
        & ~dfg["edges"]["is_self_loop"]
    ].head(8)
    print("\nDFG strongest follows")
    print(top_edges[["from_activity", "to_activity", "count", "probability"]].to_string(index=False))

    print(f"\nwrote files under {OUTPUT}")


if __name__ == "__main__":
    main()
