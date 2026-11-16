# Learner guide — Behavioral state modeling (`step03_behavioral_state_modeling.py`)

## Goal (in plain English)

Funnel **stages** are labels **you** define (`page_view` → landing).

An **HMM** asks a different question: **“What hidden reading mode is this person in right now?”** — skimming, scrolling, exploring, deep reading — inferred from the **sequence** of events.

Duration in a mode is **geometric** (chance of staying each step) — the usual HMM stand-in for a full HSMM.

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py
python day-1/03_state_modeling/step03_behavioral_state_modeling.py
```

### Tiny worked example

```bash
python day-1/03_state_modeling/examples/01_hmm_example.py
```

Needs `hmmlearn` (vendored under `marketing-behavioral-labs/day1/.vendor` if not in the env).

## Input / Output

| Input | `day-1/output/sessionized_events.csv` |
|-------|----------------------------------------|
| Outputs | `hmm_modes.csv`, `hmm_durations.csv`, `hmm_mode_transitions.csv`, `hmm_reader_modes.csv`, `sessionized_events_hmm.csv` |

---

## Big picture (intuition)

You only **see** events (page view, scroll, …). Modes are **hidden**.

The model learns:

1. How likely each mode is to **emit** each event  
2. How modes **switch** (including staying put)  
3. Then **decode** the most likely mode path for every browsing event  

```text
sessionized_events.csv
         │
         ▼
 load_sessionized_events()   ← add obs codes
         │
         ▼
 fit_hmm()                   ← train on pre-March behavior sequences
         │
         ▼
 decode_states()             ← label every browsing event
         │
         ├── mode_table / duration_table / mode_transitions
         └── reader_mode_summary → write CSVs
```

---

## High-level variables

### Path / config constants

| Name | What it is |
|------|------------|
| `DAY1` / `ROOT` / `OUTPUT` | Lab + repo paths |
| `VENDOR` | Bundled `hmmlearn` path if needed |
| `SESSIONIZED_EVENTS` | Step01 CSV |
| `VALID_END` | Train only before `2026-03-01` |
| `STATE_COLUMN` | `"hmm_state"` — integer mode id on events |
| `MINIMUM_MODE_MASS` | `0.30` — min emission mass to claim a named profile |
| `OBSERVATIONS` | Ordered event vocabulary → integer codes |
| `CONVERSION_EVENTS` | Held out of training / decoding behavior |
| `MODE_PROFILES` | Which events “belong” to skimming / scrolling / exploring / deep_reading |
| `REQUIRED_COLUMNS` | Must exist on the input CSV |

### Objects created while running

| Name | What it is |
|------|------------|
| `events` | Clickstream with `obs`, later `hmm_state` / `hmm_mode` |
| `obs` | Integer code of `event_name` in `OBSERVATIONS` |
| `model` | Fitted `CategoricalHMM` |
| `names` | `{state_id: "skimming", ...}` |
| `observations` / `lengths` | Packed sequences for hmmlearn |
| `occupied` | Share of decoded events per state (balance check) |
| `modes` / `durations` / `transitions` / `readers` | Report tables |

---

## Deep code walkthrough (every function)

### `load_sessionized_events()`

**Job:** Load sessions and encode observations.

1. Read CSV or rebuild via step01.  
2. Require cookie/time/event/`session_idx`.  
3. Reject unknown event names.  
4. Flag conversions; map `event_name` → `obs` (int).

**Returns:** Events ready for HMM.

---

### `fit_hmm(events, n_states=4, max_sessions=8000, max_length=25, seed=42)`

**Job:** Train the categorical HMM on reading sequences.

**Steps:**

1. Keep pre-`VALID_END` rows that are **not** conversions.  
2. Sample up to `max_sessions` sessions.  
3. Keep only the first `max_length` events per session (short sequences train faster).  
4. Build `observations` + `lengths` for hmmlearn.  
5. `_fit_balanced(...)` with several random restarts.  
6. `_name_modes(model)` for human labels.

**Returns:** `(model, names)`.

---

### `_fit_balanced(observations, lengths, n_states, seed, restarts=6)`

**Job:** Fit several HMMs; keep the one that is both **occupied** (no dead state) and high-scoring.

For each restart: create `CategoricalHMM`, `fit`, check min state occupancy + log-likelihood; keep best.

**Returns:** Best `CategoricalHMM`.

---

### `_name_modes(model)`

**Job:** Attach business names to latent states using emission mass on profile events.

Greedy match: highest mass to unused profile if mass ≥ `MINIMUM_MODE_MASS`. Leftovers get fallback names (`light_reading`, …).

**Returns:** `{state: mode_name}`.

---

### `_describe(probabilities)`

**Job:** Short text of top non-conversion emissions (for the modes table).

---

### `decode_states(model, events)`

**Job:** Viterbi-style most likely mode for every **browsing** event (`predict` with session lengths). Conversion rows stay `-1` / blank mode.

**Returns:** Series `hmm_state` aligned to `events`.

---

### `mode_table(model, names)`

**Job:** One row per state: name, description, start probability, mean sojourn (from self-transition), top event, full emission vector.

Mean duration ≈ `1 / (1 - stay_probability)`.

---

### `duration_table(model, names, max_duration=10)`

**Job:** Geometric P(mode lasts d events) for d = 1…10 — teaching stand-in for HSMM duration plots.

---

### `mode_transitions(model, names)`

**Job:** Flatten `transmat_` to from_mode / to_mode / probability / `is_self`.

---

### `reader_mode_summary(events, names)`

**Job:** Cookie-level view of modes.

1. Count modes per cookie → shares.  
2. Dominant mode = argmax share.  
3. Per mode: how many readers are dominated by it, mean share, overall event share.

**Returns:** Reader/mode overview table.

---

### `main()`

```text
load → fit_hmm → decode → attach hmm_mode
build mode / duration / transition / reader tables
write CSVs including sessionized_events_hmm.csv
print plain-English mode summary
```

---

## Acceptance checks

- Four modes named (or named + fallbacks)  
- Browsing events have `hmm_state` ≥ 0; conversions unassigned  
- `sessionized_events_hmm.csv` usable by step04  

## Teaching takeaway

Answer: *“How are they reading right now?”* (latent mode) — different from funnel stage *and* from long-term audience segment.
