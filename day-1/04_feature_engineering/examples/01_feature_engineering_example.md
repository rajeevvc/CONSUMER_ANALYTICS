# Example guide — Feature engineering (`01_feature_engineering_example.py`)

## Goal (in plain English)

Turn toy events into **one numeric habit vector per cookie** — visits → session scorecards → user features ready for segmentation.

Toy twin of step01 summary + `step04_feature_engineering.user_features`.

## How to run

```bash
conda activate awsproject
python day-1/04_feature_engineering/examples/01_feature_engineering_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Toy events with stages |
| **PROCESSED** | Cookie-level feature preview |

---

## Big picture (intuition)

```text
load_toy_events()
      → session_features()   one row per visit
      → user_features()      one row per anonymous_id
      → print RAW / PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `STAGE_BY_EVENT` / `STAGE_RANK` | Event → stage → depth |
| `BEHAVIOR` | Event names counted into rates |
| `CONVERSION` | Outcome events that flag `converted` |
| `sessions` | Visit-level table |
| `users` / `features` | Cookie-level vectors |
| `share_intent` / `share_deep` | Mix of visit depths |
| `*_rate` | Event share of behavior volume |
| `recency_days` / `days_active` | Freshness and span |

---

## Deep code walkthrough (every function)

### `session_features(events)`

**Job:** For each session, compute duration, behavior count, furthest stage/rank, conversion flag, and per-event counts.

### `user_features(sessions)`

**Job:** Roll sessions to cookies:

1. Means: sessions, duration, depth, conversion.  
2. Stage mix → `share_intent`, `share_deep`, `share_landing_or_scroll`.  
3. Event totals / behavior sum → `*_rate`.  
4. `days_active`, `recency_days` vs latest snapshot.

### `_section(title)` / `main()`

Print RAW; build sessions + users; print PROCESSED preview columns.

Uses: `describe_sessions()`, `load_toy_events()`, `STAGE_BY_EVENT`.

---

## Teaching takeaway

Answer: *“What does this cookie’s habit look like?”* (toy: A0001 shallow/no convert; A0004 deep/converts.)
