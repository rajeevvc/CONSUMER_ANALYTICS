# Learner guide — Journey analysis (`step02_journey_analysis.py`)

## Goal (in plain English)

Sessions alone do not say **where journeys leak**. This step builds three complementary maps:

| Method | Question | Unit |
|--------|----------|------|
| **Funnel** | How many visits reach each stage? Do they advance? | Stage |
| **Markov** | Given I’m here, where next — or exit? | Stage + `exit` |
| **DFG** | What event→event paths actually happen? | Event name |

Together they answer: **“Where should we focus to improve the path?”**

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py
python day-1/02_journey/step02_journey_analysis.py
```

### Tiny worked examples

```bash
python day-1/02_journey/examples/01_funnel_example.py
python day-1/02_journey/examples/02_markov_example.py
python day-1/02_journey/examples/03_dfg_example.py
```

## Input / Output

| Input | `day-1/output/sessionized_events.csv` |
|-------|----------------------------------------|
| Outputs | `funnel.csv`, `markov_*.csv`, `dfg_*.csv` under `day-1/output/` |

---

## Big picture (intuition)

```text
sessionized_events.csv
         │
         ▼
 load_sessionized_events()
         │
         ├── funnel_table()     → reach & advance rates
         ├── fit_markov()       → P(next stage | current) + exit
         └── fit_dfg()          → event process map, loops, top paths
```

Funnel = **ladder**. Markov = **dice at each rung**. DFG = **street map of real clicks**.

---

## High-level variables

### Path / config constants

| Name | What it is |
|------|------------|
| `DAY1` / `OUTPUT` | Lab folders |
| `SESSIONIZED_EVENTS` | Path to step01 event CSV |
| `VALID_END` | `2026-03-01` — Markov/DFG train only on earlier data |
| `MAX_VARIANT_STEPS` | Cap path length when listing common journeys (6) |
| `CONVERSION_EVENTS` / `STAGE_BY_EVENT` | Same taxonomy as step01 |
| `FUNNEL_STAGES` | Ordered ladder including registration / subscription |
| `MARKOV_STATES` | Funnel stages + artificial `exit` |
| `INTERVENING_STAGES` | Stages used to pick “biggest exit” before outcomes |

### Objects created while running

| Name | What it is |
|------|------------|
| `events` | Sessionized clickstream with `stage` |
| `funnel` | One row per stage with reach / advance |
| `counts` / `probabilities` | Markov count matrix and row-normalized probs |
| `transitions` / `dropoff` / `matrix` | Long form, exit rates, wide matrix |
| `biggest` | Intervening stage with highest exit probability |
| `dfg` | Dict of activities / edges / loops / journeys |
| `pairs` | START / event→event / END follows |

---

## Deep code walkthrough (every function)

### `load_sessionized_events()`

**Job:** Get events with sessions.

1. Read CSV, or rebuild via step01 `load_web_events` + `sessionize`.  
2. Require cookie, time, event, `session_idx`.  
3. Parse timestamps; map `stage`; flag conversions.

**Returns:** Clean events DataFrame.

---

### `funnel_table(events)`

**Job:** Measure the ladder.

**Steps:**

1. Count events per stage.  
2. Per session, mark which stages appear (`contains`).  
3. Find furthest stage index per session.  
4. For each stage: sessions containing it, sessions whose furthest stage is here, sessions that also contain the **next** stage, **advance_rate**.

**Returns:** Funnel DataFrame.

---

### `fit_markov(events)`

**Job:** First-order stage transition model + exits.

**Intuition:** Inside a session, each stage can move to another stage. The **last** stage of a session also gets an **exit** transition (left without going further in that visit).

**Steps:**

1. Keep rows before `VALID_END`; sort within session.  
2. Count consecutive stage→stage pairs **in the same session**.  
3. Add stage→`exit` for every session’s last event.  
4. Row-normalize to probabilities.  
5. Build long table, dropoff table, wide matrix.  
6. Among intervening stages with enough traffic, pick highest exit probability.

**Returns:** `(transitions, dropoff, matrix, biggest)`.

---

### `_markov_long(counts, probabilities)`

**Job:** Flatten the matrix to `from_stage`, `to_stage`, `count`, `probability` (skip empty cells; skip rows from `exit`).

---

### `_markov_dropoff(counts, probabilities)`

**Job:** Per funnel stage: how often the next “move” is **exit**.

---

### `fit_dfg(events)`

**Job:** Build the event-level process map (before March).

Calls helpers and returns:

```python
{"activities", "edges", "loops", "journeys"}
```

---

### `_directly_follows(train)`

**Job:** List every observed follow edge.

- `START → first event` of each session  
- `event → next event` inside the session  
- `last event → END`

**Returns:** Pair table with `session_idx`, `from_activity`, `to_activity`.

---

### `_edge_table(pairs)`

**Job:** Aggregate edges with strength metrics.

| Field | Meaning |
|-------|---------|
| `count` | How often this follow occurred |
| `case_count` | How many sessions saw it at least once |
| `probability` | Share of follows leaving `from_activity` |
| `dependency` | Heuristic “directed strength” (self-loops handled separately) |
| `is_self_loop` / `is_start` / `is_end` | Flags |

---

### `_activity_table(train, pairs)`

**Job:** Per event name: how often it fires, in how many sessions, how often it starts/ends a visit (`start_share`, `end_share`).

---

### `_loops(train, edges)`

**Job:** Find repetition patterns.

1. **Self-loops** — same activity twice in a row (from edges).  
2. **Return loops** — pattern `A → B → A` inside a session.

Sorted by frequency.

---

### `_variants(train)`

**Job:** List the most common **collapsed** paths (repeated same event in a row counts once), truncated to `MAX_VARIANT_STEPS`, top 20 journeys with share of sessions.

---

### `main()`

```text
load events
funnel → funnel.csv
Markov → transitions / matrix / dropoff CSVs; print biggest exit
DFG → activities / edges / loops / journeys CSVs; print top follows
```

---

## Acceptance checks

- Funnel stages follow the defined order  
- Markov rows (non-exit) roughly sum to 1 across destinations  
- DFG edges include START/END markers  

## Teaching takeaway

Answer: *“Where do journeys stall, exit, or loop — and what real click paths dominate?”*
