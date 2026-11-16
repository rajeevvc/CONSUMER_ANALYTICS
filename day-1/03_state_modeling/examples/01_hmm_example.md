# Example guide — HMM (`01_hmm_example.py`)

## Goal (in plain English)

Learn **2 hidden reading modes** from click sequences and label each browse event with the most likely mode (Viterbi/`predict`).

Toy twin of `step03_behavioral_state_modeling.py` (lab uses 4 modes; this demo uses 2 for clarity).

## How to run

```bash
python day-1/03_state_modeling/examples/01_hmm_example.py
```

Needs `hmmlearn` (vendored under `marketing-behavioral-labs/day1/.vendor` if missing).

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Browse events (conversions dropped) |
| **PROCESSED** | Same events + `hmm_mode` |

---

## Big picture (intuition)

You see events; modes are hidden. Fit emissions + transitions, then decode.

```text
load_toy_events()
      → encode()           event → integer obs
      → fit_and_decode()   2-state CategoricalHMM + names
      → print RAW / PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `VENDOR` | Optional path to bundled hmmlearn |
| `OBS` | Small event vocabulary for the demo |
| `CONVERSION` | Outcomes excluded from fitting/decoding |
| `obs` | Integer code of each browse event |
| `X` / `lengths` | Packed sequences for hmmlearn |
| `model` | Fitted `CategoricalHMM` |
| `names` | `{0/1 → skimming_like | exploring_like}` |
| `hmm_state` / `hmm_mode` | Decoded labels |

---

## Deep code walkthrough (every function)

### `encode(events)`

**Job:** Drop conversion events; map `event_name` → `obs` using `OBS`; drop unknowns.

### `fit_and_decode(events)`

**Job:**

1. Encode and sort by session/time.  
2. Fit 2-state `CategoricalHMM`.  
3. `predict` → `hmm_state`.  
4. Name modes from emission mass on page_view+scroll (higher → `skimming_like`, other → `exploring_like`).

**Returns:** `(model, decoded_frame, names)`.

### `_section(title)` / `main()`

Print RAW browse rows; fit/decode; print PROCESSED with modes.

Uses: `describe_sessions()`, `load_toy_events()`.

---

## Teaching takeaway

Answer: *“What mode is active behind this click?”* — not the same as a hand-tagged funnel stage.
