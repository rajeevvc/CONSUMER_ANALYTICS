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

## What to take into the lab

In `step02`, the same idea runs on full sessionized web events. Cliffs in `advance_rate` guide UX / content work (e.g. intent→deep paywall friction).
