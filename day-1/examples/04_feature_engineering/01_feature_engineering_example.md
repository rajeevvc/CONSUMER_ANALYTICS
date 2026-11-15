# `01_feature_engineering_example.py` — deep code walkthrough

**Question:** How do we turn visits into one numeric feature row per cookie?

**Maps to lab:** `day-1/step04_feature_engineering.py`

**Run:**

```bash
conda activate awsproject
python day-1/examples/04_feature_engineering/01_feature_engineering_example.py
```

---

## Why this exists

Segmentation cannot cluster raw event streams directly. You need a **fixed-width vector per cookie**:

- How often do they visit? (`n_sessions`, `days_active`)
- How recently? (`recency_days`)
- How deep / engaged? (`mean_furthest_rank`, event rates)
- Do they convert? (`conversion_rate`)

This example shows the two-level transform:

```
events  →  session features  →  user (cookie) features
```

---

## Input

`toy_sessions.load_toy_events()` — 4 sessions, 4 cookies (one session each).

Constants:

| Name | Role |
|------|------|
| `STAGE_RANK` | landing=1 … deep=5 |
| `BEHAVIOR` | Event types counted as browsing |
| `CONVERSION` | Outcome event names |

---

## Function 1: `session_features(events)`

**Output grain:** one row per `session_idx`.

### Per-session loop

For each session:

1. Mark conversion rows via `is_conversion`.
2. Keep **behavior** rows for depth/duration/counts.
3. Compute:
   - `session_start` = min timestamp (all events)
   - `duration_sec` = last behavior ts − first behavior ts (0 if no behavior)
   - `n_behavior_events`
   - `furthest_rank` / `furthest_stage` from max stage rank on behavior
   - `converted` = any conversion event in the session
   - counts for each name in `BEHAVIOR` (`page_view`, `scroll`, …)

### Why behavior-only depth?

Conversion outcomes should not inflate “how deep did they browse?” the same way checkout events do via stage ranks in `BEHAVIOR`.

### Toy intuition

| Session | Duration | Furthest | Converted |
|---------|----------|----------|-----------|
| S1 | ~0s | landing | False |
| S2 | ~60s | engaged | False |
| S3 | ~150s | intent | False |
| S4 | ~240s | deep | True |

---

## Function 2: `user_features(sessions)`

**Output grain:** one row per `anonymous_id`.

### Aggregate means / rates

```python
n_sessions, mean_duration_sec, mean_behavior_events,
mean_furthest_rank, conversion_rate,
first_session, last_session
```

### Stage-share features

Build cookie × furthest_stage counts, then:

```
share_intent = sessions ending at intent / all sessions
share_deep   = sessions ending at deep / all sessions
share_landing_or_scroll = …
```

In this toy each cookie has **one** session, so shares are 0 or 1.

### Event mix rates

Sum event counts across sessions, divide by total behavior events:

```
page_view_rate, scroll_rate, …, subscription_view_rate, …
```

### Time features

```
days_active  = (last_session - first_session) in days
recency_days = (global max last_session - this cookie's last_session) in days
```

On a single-day toy, `days_active` is 0 and `recency_days` is small offsets between session starts.

---

## What `main()` prints

| Section | Content |
|---------|---------|
| OUTPUT 1 | Session feature table + row walk |
| OUTPUT 2 | User feature table + row walk |
| OUTPUT 3 | Acceptance checks |

### Acceptance expectations

| Check | Expect |
|-------|--------|
| `n_sessions` unique | `{1}` |
| A0004 `conversion_rate` | `1.0` |
| A0001 `mean_furthest_rank` | `1.0` |
| A0004 `mean_furthest_rank` | `5.0` |

---

## Feature families (mental model)

| Family | Examples | Used for |
|--------|----------|----------|
| Frequency | `n_sessions`, `days_active` | Loyalty / volume |
| Recency | `recency_days` | Freshness |
| Engagement | `mean_duration_sec`, `mean_furthest_rank`, `*_rate` | Intensity / mix |
| Outcome | `conversion_rate` | Value |

These are exactly the kinds of columns later passed to `StandardScaler` + clustering.

---

## Lab connection

`step04` applies the same rollup on full session tables from `step01`, often with more columns (device mix, referrer mix, HMM mode shares). The toy strips to the teaching core.

## Next step

`05_segmentation` clusters **user-level** vectors. It uses a synthetic 12-cookie audience so groups are obvious; conceptually those vectors come from this feature step.
