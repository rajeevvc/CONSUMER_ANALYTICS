# `01_funnel_example.py` — deep code walkthrough

**Question:** How many sessions reached each stage, and how many advanced to the next?

**Maps to lab:** `day-1/step02_journey_analysis.py` → `funnel_table`

**Run:**

```bash
conda activate awsproject
python day-1/examples/02_journey/01_funnel_example.py
```

---

## Why this exists

A **funnel** answers depth questions:

- How many visits ever hit landing / scroll / intent / deep?
- Where is the cliff (advance rate collapses)?
- How many visits *ended* at each stage (furthest stage)?

It does **not** answer “what was the immediate next click?” That is Markov.

---

## Input

From `examples/_shared/toy_sessions.py` → `load_toy_events()`.

Four hand-built sessions (already “sessionized”):

| Session | Story | Stages touched |
|---------|-------|----------------|
| S1 | Bounce | landing |
| S2 | Engaged reader | landing → scroll → engaged |
| S3 | Intent cliff | … → intent |
| S4 | Converter | … → deep → subscription |

Each event already has `stage` via `STAGE_BY_EVENT`.

`FUNNEL_STAGES` ladder:

```
landing → scroll → engaged → intent → deep → registration → subscription
```

---

## Core function: `funnel_table(events)`

### Step A — event counts per stage

```python
event_counts = events.groupby("stage").size()
```

How many *events* mapped to each stage (not sessions).

### Step B — session × stage presence matrix

```python
presence = events.groupby(["session_idx", "stage"]).size().unstack(fill_value=0)
contains = presence[FUNNEL_STAGES].gt(0)
```

`contains[stage]` is True if that session **ever** had ≥1 event at that stage.

Missing stages get a zero column so the ladder is complete.

### Step C — furthest stage per session

```python
rank = {stage: index for index, stage in enumerate(FUNNEL_STAGES)}
furthest = events["stage"].map(rank).groupby(session_idx).max()
```

`sessions_ending_here` = count of sessions whose max rank equals this stage’s index.

### Step D — advance rate

For stage *i* with next stage *j*:

```
advanced = sessions that contain i AND contain j
advance_rate = advanced / sessions_containing_i
```

**Critical teaching point:** advance is **co-occurrence** (“ever also reached next”), **not** “next consecutive event was next stage.”

Example: a session can hit `intent` then later `deep` with other events in between; funnel still counts it as advancing intent→deep.

### Output columns

| Column | Meaning |
|--------|---------|
| `stage` | Funnel rung |
| `events` | Event count at this stage |
| `sessions_containing_stage` | Visits that ever touched it |
| `sessions_ending_here` | Visits whose furthest stage is here |
| `next_stage` | Next rung (or null at top) |
| `advance_rate` | Share that also touched next rung |

---

## Toy numbers you should see

| Stage | Containing | Advance rate intuition |
|-------|------------|------------------------|
| landing | 4 | 3 also scrolled → **0.75** |
| scroll | 3 | all 3 engaged → **1.0** |
| engaged | 3 | 2 also intent → **~0.67** |
| intent | 2 | 1 also deep → **0.50** (cliff) |
| deep | 1 | registration unused in toy → **0.0** |

S1 ends at landing; S2 at engaged; S3 at intent; S4 reaches subscription (ends there as furthest among ladder ranks that appear).

---

## `main()` narration

1. Print input events + per-session stage chains.
2. Build and print the funnel table with column glossary.
3. Walk each row with interpretations for landing and intent cliffs.
4. Acceptance checks on `0.75` and `0.50`.

---

## Funnel vs Markov vs DFG

| Method | Grain | Question |
|--------|-------|----------|
| **Funnel** | Stage presence | Ever reached? Advanced to next rung? |
| **Markov** | Consecutive stages + exit | What happens *right after* this stage? |
| **DFG** | Raw event names | What exact click→click edges exist? |

---

## Sample terminal output (what you see when you run it)

### OUTPUT 1 — Input events with stages

```text
 session_idx anonymous_id           timestamp          event_name        stage
           1        A0001 2026-01-10 10:00:00           page_view      landing
           2        A0002 2026-01-10 11:00:00           page_view      landing
           2        A0002 2026-01-10 11:00:30              scroll       scroll
           …
           4        A0004 2026-01-10 13:05:00 subscription_active subscription

Per-session stages touched
  S1: landing
  S2: landing → scroll → engaged
  S3: landing → scroll → engaged → intent
  S4: landing → scroll → engaged → intent → deep → subscription
```

**How to read it:** Each event already has a `stage`. The per-session chains show depth without yet computing rates — S1 never leaves landing; S4 reaches the top of the ladder.

---

### OUTPUT 2 — Funnel table

```text
       stage  events  sessions_containing_stage  sessions_ending_here   next_stage  advance_rate
     landing       4                          4                     1       scroll        0.7500
      scroll       3                          3                     0      engaged        1.0000
     engaged       3                          3                     1       intent        0.6667
      intent       3                          2                     1         deep        0.5000
        deep       2                          1                     0 registration        0.0000
registration       0                          0                     0 subscription           NaN
subscription       1                          1                     1          NaN           NaN
```

**How to read each column:**

| Column | This run means |
|--------|----------------|
| `events` | How many clicks mapped to that stage (intent has 3 events across S3+S4) |
| `sessions_containing_stage` | How many visits *ever* hit it (landing=4, intent=2) |
| `sessions_ending_here` | Whose furthest stage is here (1 bounce at landing, 1 stuck at intent, …) |
| `advance_rate` | Of those who hit this stage, what share also hit the *next* rung |

**Key story in the numbers:** landing→scroll advance `0.75` (3 of 4 scrolled). intent→deep advance `0.50` — the **cliff**: half of intent visits never reach checkout depth.

---

### OUTPUT 3 — Row-by-row reading

```text
  landing
    events=4, sessions_with_stage=4, ended_here=1
    next=scroll, advance_rate=0.75
    interpret: 4 sessions landed; 3 also scrolled → 0.75

  intent
    events=3, sessions_with_stage=2, ended_here=1
    next=deep, advance_rate=0.5
    interpret: 2 sessions reached intent; only 1 also hit deep → 0.50 (cliff)
```

**How to read it:** Same table, narrated. `ended_here=1` at intent is S3 (looked at subscribe UI, left). S4 is the one that also hit deep.

---

### OUTPUT 4 — Acceptance checks

```text
  landing advance_rate = 0.75  (expect 0.75)
  intent advance_rate  = 0.5  (expect 0.50)
```

**How to read it:** Confirms the two teaching numbers. If these fail, the stage tags or presence logic drifted.

---

## What to take into the lab

In `step02`, the same idea runs on full sessionized web events. Cliffs in `advance_rate` guide UX / content work (e.g. intent→deep paywall friction).
