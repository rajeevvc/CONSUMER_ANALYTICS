# `02_markov_example.py` — deep code walkthrough

**Question:** Given the current stage, where do people go next — or exit the visit?

**Maps to lab:** `day-1/step02_journey_analysis.py` → `fit_markov`

**Run:**

```bash
conda activate awsproject
python day-1/examples/02_journey/02_markov_example.py
```

---

## Why this exists

A **first-order Markov chain** on stages models:

\[
P(\text{next stage} \mid \text{current stage})
\]

including a special absorbing-like sink: **`exit`** (visit ended).

Unlike Funnel (ever-reached co-occurrence), Markov only counts **consecutive** stage steps inside a session, plus one exit edge after the last event.

---

## Input

Same toy as Funnel: `toy_sessions.load_toy_events()` — 4 sessions with `stage` tags.

State space:

```python
MARKOV_STATES = FUNNEL_STAGES + ["exit"]
# landing, scroll, engaged, intent, deep, registration, subscription, exit
```

---

## Core function: `fit_markov(events)`

### Step A — order events and encode stages as ints

```python
train = events.sort_values(["session_idx", "timestamp"], kind="mergesort")
stage = train["stage"].map({name: i for i, name in enumerate(MARKOV_STATES)}).to_numpy()
session = train["session_idx"].to_numpy()
```

### Step B — count consecutive within-session transitions

```python
same = session[1:] == session[:-1]
np.add.at(counts, (stage[:-1][same], stage[1:][same]), 1)
```

Only pairs where the **same session** continues are counted. Crossing a session boundary does **not** create a transition.

Example inside S4 (stages):

```
landing → scroll → engaged → intent → deep → deep → subscription
```

That contributes edges like `landing→scroll`, `scroll→engaged`, …, `deep→deep`, `deep→subscription`.

### Step C — add stage → exit for every session’s last event

```python
is_last[:-1] = session[1:] != session[:-1]
is_last[-1] = True
np.add.at(counts, (stage[is_last], exit_i), 1)
```

Toy endings:

| Session | Last stage | Exit edge |
|---------|------------|-----------|
| S1 | landing | landing→exit |
| S2 | engaged | engaged→exit |
| S3 | intent | intent→exit |
| S4 | subscription | subscription→exit |

### Step D — row-normalize to probabilities

```python
probs = counts / row_totals   # where total > 0
```

Each row of the count matrix becomes a distribution over next states.

### Step E — return two tables

1. **Transition matrix** — rows = funnel stages (not exit), columns = all states including exit. Rounded to 3 decimals.
2. **Drop-off table** — per stage: total outbound transitions, exit count, `exit_probability`.

---

## How to read the matrix

- Pick a **row** = “I am currently at this stage.”
- Read across = probability of each next stage **or exit**.
- Row should sum ≈ 1.0.

Highlighted toy expectations:

| Cell | Expect | Why |
|------|--------|-----|
| `P(scroll \| landing)` | `0.75` | 3 of 4 landing departures go to scroll |
| `P(exit \| landing)` | `0.25` | S1 bounce |
| `P(exit \| engaged)` | `~0.333` | S2 ends at engaged among engaged’s outbound mass |

---

## Drop-off table columns

| Column | Meaning |
|--------|---------|
| `stage` | Current stage |
| `transitions` | Sum of outbound counts (includes exits) |
| `exits` | Count of stage→exit |
| `exit_probability` | `exits / transitions` |

If `transitions == 0` (stage never observed as a “from”), probability stays 0.

---

## Funnel vs Markov (same data, different math)

| | Funnel | Markov |
|-|--------|--------|
| Unit | Session presence | Consecutive stage step |
| Advance | Ever hit stage *and* next | Immediate next (or exit) |
| Exit | Implicit via “ending here” | Explicit `exit` state |
| Use | Depth / cliff overview | Path dynamics / drop-off timing |

Example: Funnel `intent→deep` advance = 0.50 means half of intent sessions also eventually hit deep. Markov `P(deep|intent)` asks only about the *next* stage after an intent event (and may also include intent→intent, intent→exit, etc.).

---

## Sample terminal output (what you see when you run it)

### RAW — stage sequence per session

```text
  S1: landing → exit
  S2: landing → scroll → engaged → exit
  S3: landing → scroll → engaged → intent → intent → exit
  S4: landing → scroll → engaged → intent → deep → deep → subscription → exit
```

**How to read it:** Consecutive stages Markov will count, plus `exit` after each visit ends.

### PROCESSED — transition matrix

```text
              landing  scroll  engaged  intent   deep  registration  subscription   exit
landing           0.0    0.75      0.0   0.000  0.000           0.0           0.0  0.250
scroll            0.0    0.00      1.0   0.000  0.000           0.0           0.0  0.000
engaged           0.0    0.00      0.0   0.667  0.000           0.0           0.0  0.333
intent            0.0    0.00      0.0   0.333  0.333           0.0           0.0  0.333
deep              0.0    0.00      0.0   0.000  0.500           0.0           0.5  0.000
registration      0.0    0.00      0.0   0.000  0.000           0.0           0.0  0.000
subscription      0.0    0.00      0.0   0.000  0.000           0.0           0.0  1.000

Note: landing→scroll=0.75, landing→exit=0.25.
```

**How to read it:** Pick a row (current stage); cells are P(next). Landing goes to scroll 75% or exit 25%.

## What to take into the lab

`step02` builds the same count → probability machinery on production-scale sessionized stages. High `exit_probability` at mid-funnel stages is a practical drop-off signal.
