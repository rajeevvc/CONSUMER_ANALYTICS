# `_shared/` — toy inputs used by the examples

These modules are **not** algorithms. They are tiny, hand-built datasets so every example can be checked on a whiteboard.

| File | Used by | What it provides |
|------|---------|------------------|
| `toy_raw_events.py` | `01_sessionize` | Raw clicks **without** `session_id` |
| `toy_sessions.py` | Journey, HMM, Features | Already-sessionized mini journeys |

Examples never read `day-1/data/web_events.csv`.

---

## `toy_raw_events.py`

### Purpose

Feed the sessionize demo with intentional edge cases:

1. Near-duplicate click (≤2s)
2. Idle gap > 30 minutes → new session
3. A converting cookie

### Schema of `load_raw_events()`

`anonymous_id`, `timestamp`, `event_name`, `content_id`, `device_type`, `referrer`

### Cookie stories

| Cookie | Design |
|--------|--------|
| A0001 | dup page_view (+1s), scroll (+5m), page_view (+35m) → 2 sessions after rules |
| A0002 | page_view → scroll → engaged_read |
| A0003 | path into intent (`subscription_view`, `subscribe_click`) |
| A0004 | path into checkout + `subscription_active` |

`describe_raw()` only prints this teaching summary.

---

## `toy_sessions.py`

### Purpose

Four finished visits for Journey / HMM / Features — small enough to compute Funnel, Markov, and DFG by hand.

### Constants

- `STAGE_BY_EVENT` — event → funnel stage map (same ladder as the lab)
- `FUNNEL_STAGES` — ordered stage list including registration/subscription

### Schema of `load_toy_events()`

| Column | Meaning |
|--------|---------|
| `session_idx` | 1…4 visit id |
| `timestamp` | Event time |
| `event_name` | Raw action |
| `anonymous_id` | `A0001`…`A0004` derived from session |
| `stage` | Mapped funnel tag |

### Session stories

| S | Path | Teaching role |
|---|------|---------------|
| 1 | page_view only | Bounce |
| 2 | → engaged_read | Engaged exit |
| 3 | → subscribe_click | Intent cliff |
| 4 | → subscription_active | Full convert path |

`describe_sessions()` prints the same summary used at the top of Journey/HMM/Features terminals.

---

## Why two toys?

| Need | Toy |
|------|-----|
| Prove 30-min cut + dedupe | Raw events (`toy_raw_events`) |
| Prove Funnel/Markov/DFG/HMM/features math | Sessionized journeys (`toy_sessions`) |

Segmentation uses a **third** synthetic audience built inside `05_segmentation/01_segmentation_example.py` (`toy_audience`) because clustering needs more than 4 points.
