# Example guide — Markov (`02_markov_example.py`)

## Goal (in plain English)

Given the **current stage**, what is the chance of each **next stage** — or **exit** (left the visit)?

Toy twin of `step02_journey_analysis.fit_markov`.

## How to run

```bash
python day-1/02_journey/examples/02_markov_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Stage sequence per session (`… → exit`) |
| **PROCESSED** | Transition matrix (rows ≈ probabilities) |

---

## Big picture (intuition)

Funnel counts reach. Markov asks: *standing on this rung, where does the next step go?*

The last stage of every session also gets an artificial move to **`exit`**.

```text
load_toy_events() → fit_markov() → print sequences + matrix
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `FUNNEL_STAGES` | Stage ladder |
| `MARKOV_STATES` | Funnel stages + `exit` |
| `counts` | Integer from→to transition counts |
| `probs` / `matrix` | Row-normalized probabilities |
| `dropoff` | Per-stage exit counts/probabilities |
| `same` / `is_last` | Same-session consecutive pairs; last event flags |

---

## Deep code walkthrough (every function)

### `fit_markov(events)`

**Job:** Count consecutive stage→stage pairs inside sessions; add stage→exit on each session’s last event; normalize rows; return matrix + dropoff table.

### `_section(title)` / `main()`

Print RAW stage paths; fit; print PROCESSED matrix.

Uses: `describe_sessions()`, `load_toy_events()`.

---

## Teaching takeaway

Answer: *“From here, where next — or out?”* (toy: landing→scroll ≈ 0.75, landing→exit ≈ 0.25.)
