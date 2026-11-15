# `01_hmm_example.py` — deep code walkthrough

**Question:** What hidden reading mode is active behind each click?

**Maps to lab:** `day-1/step03_behavioral_state_modeling.py` (Categorical HMM)

**Run:**

```bash
conda activate awsproject
python day-1/examples/03_state_modeling/01_hmm_example.py
```

---

## Why this exists

Funnel/Markov stages are **rules** you define (`page_view` → landing). An **HMM** learns **latent modes** from sequences:

- You observe events.
- You do **not** observe the mode (skimming vs exploring).
- The model infers modes that best explain the sequences.

Toy uses **2 modes** so emissions stay readable. The full lab uses **4 modes**, a larger event alphabet, and multiple random restarts.

---

## Dependencies / vendor path

```python
VENDOR = .../marketing-behavioral-labs/day1/.vendor
from hmmlearn.hmm import CategoricalHMM
```

If the vendor folder exists, it is prepended to `sys.path` so `hmmlearn` resolves like the lab environment.

---

## Input

`toy_sessions.load_toy_events()` again.

Observation alphabet `OBS` (integer codes 0…6):

| Code | Event |
|------|-------|
| 0 | page_view |
| 1 | scroll |
| 2 | engaged_read |
| 3 | subscription_view |
| 4 | subscribe_click |
| 5 | checkout_start |
| 6 | payment_success |

`CONVERSION = {subscription_active, register_complete}` is **dropped** before training — outcomes are not browsing behavior for mode learning.

---

## Function 1: `encode(events)`

1. Drop conversion outcome rows.
2. Map `event_name` → integer `obs` via `OBS`.
3. Drop rows that failed to map (`dropna` on `obs`).
4. Cast `obs` to `int`.

Returns a clean sequence table ready for hmmlearn.

---

## Function 2: `fit_and_decode(events)`

### Prepare sequence lengths

hmmlearn expects:

- `X`: shape `(n_events, 1)` of observation ints  
- `lengths`: how many events belong to each session, in order  

```python
lengths = work.groupby("session_idx").size().to_numpy()
X = work["obs"].to_numpy().reshape(-1, 1)
```

Sessions are treated as separate sequences (no transition across session boundaries).

### Model construction

```python
CategoricalHMM(
    n_components=2,      # latent modes
    n_features=len(OBS), # observation alphabet size
    n_iter=50,           # EM iterations
    tol=1e-3,
    random_state=42,     # reproducible init
)
```

**What is initialized randomly (seeded)?**

- start probabilities \(\pi\)
- transition matrix \(A\) = P(mode→mode)
- emission matrix \(B\) = P(event | mode)

**What does `fit` do?** Baum–Welch (EM) updates \(A\), \(B\), \(\pi\) to raise likelihood of the observed sequences.

**What does `predict` do?** Viterbi decoding — most likely mode sequence given the learned parameters.

### Naming modes after fit

Numeric states 0/1 are arbitrary. The code labels them by emission mass on skim-like events:

```python
skim_mass = P(page_view|mode) + P(scroll|mode)
# higher skim_mass → "skimming_like"
# other → "exploring_like"
```

Then `hmm_mode` is attached to each event.

---

## What the printed outputs mean

### Emissions `model.emissionprob_`

Rows = modes, columns = events. Cell = \(P(\text{event} \mid \text{mode})\).

Skimming-like modes put more mass on early browse events; exploring-like modes shift mass toward deeper actions.

### Transitions `model.transmat_`

\(P(\text{next mode} \mid \text{current mode})\). High diagonal ⇒ modes persist for several clicks.

### Start `model.startprob_`

\(P(\text{start in mode})\).

### Decoded table

Each event gets `hmm_mode`. Per-session paths show mode switching, e.g.:

```
S2: skimming_like → exploring_like → exploring_like
```

Exact labels can flip if EM lands in a symmetric solution; naming by skim mass keeps them interpretable.

---

## Lab vs this toy

| | This example | Day 1 lab (`step03`) |
|-|--------------|----------------------|
| Modes | 2 | 4 |
| Alphabet | 7 events | ~12 events |
| Restarts | single `random_state=42` | multiple restarts, pick best |
| Goal | Readable whiteboard demo | Production-ish fit quality |

---

## HMM vs rule stages

| | Stages (Funnel/Markov) | HMM modes |
|-|------------------------|-----------|
| Defined by | Human mapping rules | Learned from data |
| Granularity | Fixed ladder | Soft behavioral regimes |
| Use | Reporting / UX cliffs | Behavioral state features |

---

## What to take into the lab

Decoded modes can become session/user features (time in mode, switches) that later enrich segmentation — optional, not required for K-Means/GMM in the toy segmentation example.
