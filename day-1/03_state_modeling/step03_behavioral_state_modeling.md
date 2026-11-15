# Learner guide — Behavioral state modeling (`step03_behavioral_state_modeling.py`)

## Goal

Fit a **categorical Hidden Markov Model (HMM)** on click sequences to recover **latent reading modes** (skimming, scrolling, exploring, deep_reading). Label every browsing event with the most likely mode.

Stages are rules you define; HMM modes are **inferred** from sequences. Duration is **geometric** via self-transitions (HMM stand-in for HSMM).

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

Needs `hmmlearn` (vendored under `marketing-behavioral-labs/day1/.vendor` if missing from the env).

## Input / Output

| Input | `day-1/output/sessionized_events.csv` |
|-------|----------------------------------------|
| Outputs | `hmm_modes.csv`, `hmm_durations.csv`, `hmm_mode_transitions.csv`, `hmm_reader_modes.csv`, `sessionized_events_hmm.csv` |

---

## Deep code walkthrough

### Bootstrap

```python
DAY1 = parents[1]
ROOT = DAY1.parent
VENDOR = ROOT / "marketing-behavioral-labs" / "day1" / ".vendor"
sys.path ← 01_sessionize + optional VENDOR
from hmmlearn.hmm import CategoricalHMM
```

| Constant | Role |
|----------|------|
| `OBSERVATIONS` | Fixed event alphabet → integer codes |
| `MODE_PROFILES` | Event groups used to **name** learned states |
| `MINIMUM_MODE_MASS` | `0.30` — min emission mass to claim a profile name |
| `VALID_END` | Train on `timestamp < 2026-03-01` |

---

### `load_sessionized_events()`

Load (or rebuild) sessions; require cookie/time/event/`session_idx`; map `obs` ints; flag conversions. Unknown event names raise (taxonomy lock).

---

### `fit_hmm(events, n_states=4, ...)`

1. Keep pre-March **non-conversion** events.  
2. Sample ≤ `max_sessions` (8000) sessions; keep ≤ `max_length` (25) events each.  
3. Build `observations` matrix + `lengths` array for hmmlearn.  
4. `_fit_balanced` — 6 random restarts (`random_state=seed+restart`):
   - fit `CategoricalHMM`  
   - score likelihood  
   - prefer models whose states are **occupied** (min occupancy, then score)  
5. `_name_modes` — match emission mass to `MODE_PROFILES` greedily; leftovers get fallback names (`light_reading`, …).

**Why restarts?** EM can land in poor local optima; balanced occupancy avoids empty modes.

---

### `decode_states(model, events)`

Viterbi (`model.predict`) on behavior events only. Conversion rows stay `-1` / empty mode.

Implementation detail: sort behavior by session+time, compute per-session lengths, predict, then **unpermute** back to original row order.

---

### Reporting helpers

| Function | Output idea |
|----------|-------------|
| `mode_table` | Emissions, start π, mean sojourn `1/(1-p_stay)`, top event |
| `duration_table` | Geometric P(duration=d) = `p_stay^(d-1) * (1-p_stay)` |
| `mode_transitions` | Full A matrix as long rows |
| `reader_mode_summary` | Per cookie dominant mode + event shares |

`_describe` builds a short human string of top non-conversion emissions ≥5%.

---

### `main()`

```text
load → fit_hmm → decode → attach hmm_state / hmm_mode
     → write 5 CSVs → print mode overview
```

`sessionized_events_hmm.csv` is what step04 optionally joins for `hmm_share_*` features.

---

## Acceptance checks

- Conversion events have no mode (empty / -1)  
- Every behavior event has an `hmm_mode`  
- Feature engineering can join HMM shares from the HMM events CSV  

## Teaching takeaway

Answer: *“What reading mode is happening inside this visit?”* (sequence / latent state)
