# Example guide — Funnel (`01_funnel_example.py`)

## Goal (in plain English)

From staged events, build a **ladder**: how many sessions reached each stage, and what share also reached the **next** stage (`advance_rate`).

Toy twin of `step02_journey_analysis.funnel_table`.

## How to run

```bash
python day-1/02_journey/examples/01_funnel_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Toy events with `stage` |
| **PROCESSED** | Funnel table (reach + advance) |

---

## Big picture (intuition)

A funnel is not “next click.” It asks: *did this visit ever touch stage X, and also ever touch stage X+1?*

```text
load_toy_events() → funnel_table() → print RAW / PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `FUNNEL_STAGES` | Ordered ladder from `_shared/toy_sessions` |
| `events` | Toy sessionized events with stages |
| `presence` / `contains` | Which stages appear in each session |
| `furthest` | Deepest stage index per session |
| `table` | Final funnel DataFrame |
| `advance_rate` | Containing-next / containing-this |

---

## Deep code walkthrough (every function)

### `funnel_table(events)`

**Job:** Build the scorecard.

1. Count events per stage.  
2. Mark stages present in each session.  
3. Find furthest stage per session.  
4. For each stage: sessions containing it, ending here, advance rate to next.

### `_section(title)` / `main()`

Print banners; load toys; show RAW events; print PROCESSED funnel.

Uses: `describe_sessions()`, `load_toy_events()`, `FUNNEL_STAGES`.

---

## Teaching takeaway

Answer: *“Where does the ladder thin out?”* (toy note: landing→scroll strong; intent→deep is the cliff.)
