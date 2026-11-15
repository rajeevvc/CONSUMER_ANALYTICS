# Learner guide — Journey analysis (`step02_journey_analysis.py`)

## Goal

From sessionized events, build three complementary journey views:

| Method | Question | Unit |
|--------|----------|------|
| **Funnel** | How many sessions reach each stage? Advance rate? | Stage |
| **Markov** | Given current stage, where next (or exit)? | Stage + `exit` |
| **DFG** | What event→event paths actually happen? | Event name |

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py          # if not already done
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

## Deep code walkthrough

### Bootstrap

```python
DAY1 = Path(__file__).resolve().parents[1]
OUTPUT = DAY1 / "output"
sys.path.insert(0, str(DAY1 / "01_sessionize"))  # optional rebuild import
```

`VALID_END = 2026-03-01` — Markov/DFG train only on events **before** this date (hold out March as a test window). Funnel uses all loaded events.

Taxonomy constants (`STAGE_BY_EVENT`, `FUNNEL_STAGES`, `MARKOV_STATES`) must stay in sync with step01.

---

### `load_sessionized_events()`

1. Prefer `sessionized_events.csv`.  
2. If missing → `from step01_sessionize import load_web_events, sessionize` and rebuild.  
3. Require `anonymous_id`, `timestamp`, `event_name`, `session_idx`.  
4. Re-map `stage` and `is_conversion` (safe even if CSV already has them).

---

### Funnel — `funnel_table(events)`

1. Count events per stage.  
2. Build session×stage **presence** matrix (`>0`).  
3. Furthest stage = max ladder index per session.  
4. For each stage *i*:
   - `sessions_containing_stage`  
   - `sessions_ending_here` (furthest == *i*)  
   - `advance_rate` = share that also contain stage *i+1*  

**Advance is co-occurrence**, not “next click was next stage.” Cliffs show where journeys stall.

---

### Markov — `fit_markov(events)`

Train subset: `timestamp < VALID_END`.

1. Encode stages as ints (`MARKOV_STATES` includes `exit`).  
2. Count consecutive pairs **within the same session** via `np.add.at`.  
3. For every session’s last event, add `stage → exit`.  
4. Row-normalize → probabilities.  
5. Build:
   - long `transitions`  
   - wide `matrix` (rows = funnel stages, cols = stages+exit)  
   - `dropoff` with `exit_probability`  
6. Pick `biggest` drop-off among intervening stages with enough mass (`≥1000` transitions).

Helpers `_markov_long` / `_markov_dropoff` only reshape the count/probability arrays.

---

### DFG — `fit_dfg(events)`

Same pre-March window. Works on **`event_name`**, not stages.

#### `_directly_follows`

Three edge families: `START→first`, consecutive pairs, `last→END`.

#### `_edge_table`

- `count`, `case_count` (unique sessions with that edge)  
- `probability` = outbound share from `from_activity`  
- Heuristic `dependency` (process-mining style forward vs reverse strength)  
- Flags: self-loop / start / end  

#### `_activity_table`

Per event name: event count, session count, how often it starts/ends a visit.

#### `_loops`

- Self-loops from edges  
- Return loops of form `A > B > A` inside a session (length-3 windows)

#### `_variants`

Collapse consecutive repeats; take first `MAX_VARIANT_STEPS` (6) events; append `END`; return top 20 paths by frequency.

---

### `main()`

```text
load events
  → funnel_table → funnel.csv
  → fit_markov → markov_*.csv
  → fit_dfg → dfg_*.csv
  → print funnel, matrix, top DFG edges
```

---

## Acceptance checks

- Funnel / Markov use **stages**; DFG uses **event names**  
- Intent → deep advance much lower than earlier steps (cliff)  
- Markov matrix rows roughly sum to 1  

## Teaching takeaway

Funnel = reach; Markov = next-step odds; DFG = fine-grained click map.
