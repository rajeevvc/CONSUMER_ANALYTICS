# Example guide — HMM (`01_hmm_example.py`)

## Goal (in plain English)

Learn **2 hidden reading modes** from click sequences and label each browse event with the most likely mode (Viterbi/`predict`).

Toy twin of `step03_behavioral_state_modeling.py` (lab uses 4 modes; this demo uses 2 for clarity).

## How to run

```bash
python day-1/03_state_modeling/examples/01_hmm_example.py
```

Needs `hmmlearn` (vendored under `marketing-behavioral-labs/day1/.vendor` if missing).

## Sample input & output

Source: `_shared/data/toy_sessions.csv` (conversion outcomes dropped before fit/decode).

### INPUT (RAW)

| Column | Meaning |
|--------|---------|
| `session_idx` | Visit id (HMM sequences are per session) |
| `event_name` | Browse action coded as an observation (`obs`) |
| `stage` | Funnel tag (for reading only; HMM learns from `event_name`) |

Conversion events (`subscription_active`, `register_complete`) are dropped before fit/decode.

```text
 session_idx        event_name   stage
           1         page_view landing
           2         page_view landing
           2            scroll  scroll
           2      engaged_read engaged
           3         page_view landing
           3            scroll  scroll
           3      engaged_read engaged
           3 subscription_view  intent
           3   subscribe_click  intent
           4         page_view landing
           4            scroll  scroll
           4      engaged_read engaged
           4 subscription_view  intent
           4    checkout_start    deep
           4   payment_success    deep
```

### OUTPUT (PROCESSED)

One row per **browse event** (same grain as input, plus the decoded mode):

| Column | Meaning |
|--------|---------|
| `session_idx` | Visit id |
| `event_name` | Original browse action |
| `hmm_mode` | Most likely latent mode (`skimming_like` or `exploring_like`) |

```text
 session_idx        event_name       hmm_mode
           1         page_view  skimming_like
           2         page_view  skimming_like
           2            scroll exploring_like
           2      engaged_read exploring_like
           3         page_view  skimming_like
           3            scroll exploring_like
           3      engaged_read exploring_like
           3 subscription_view exploring_like
           3   subscribe_click exploring_like
           4         page_view  skimming_like
           4            scroll exploring_like
           4      engaged_read exploring_like
           4 subscription_view exploring_like
           4    checkout_start exploring_like
           4   payment_success exploring_like
```

**Read it:** 2 modes — `page_view` usually `skimming_like`; deeper clicks `exploring_like`.

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
