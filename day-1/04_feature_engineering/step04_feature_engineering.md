# Learner guide — Feature engineering (`step04_feature_engineering.py`)

## Goal (in plain English)

Sessions and HMM labels are still **visit-level** or **event-level**.

Models like segmentation need **one scorecard per cookie**: how often they visit, how deep they go, how often they convert, device mix, and (optionally) HMM mode mix.

This step builds:

1. **Session features** — enrich each visit  
2. **User features** — roll visits up to `anonymous_id`

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py
python day-1/03_state_modeling/step03_behavioral_state_modeling.py   # optional — hmm_share_*
python day-1/04_feature_engineering/step04_feature_engineering.py
```

### Tiny worked example

```bash
python day-1/04_feature_engineering/examples/01_feature_engineering_example.py
```

## Input / Output

| Input | Role |
|-------|------|
| `day-1/output/sessions.csv` | Required |
| `day-1/output/sessionized_events_hmm.csv` | Optional HMM mode shares |

| Output | Grain |
|--------|--------|
| `day-1/output/session_features.csv` | One row per session |
| `day-1/output/user_features.csv` | One row per cookie |

---

## Big picture (intuition)

```text
sessions.csv  (+ optional HMM events)
        │
        ▼
 load_sessions()
        │
        ▼
 enrich_session_features()   ← tenure, timing, depth flags, hmm shares
        │
        ▼
 user_features()             ← one vector per anonymous_id
        │
        ▼
 write session_features.csv + user_features.csv
```

Think: **visits → habits**. Step05 clusters those habit vectors.

---

## High-level variables

### Path / config constants

| Name | What it is |
|------|------------|
| `DAY1` / `OUTPUT` | Lab folders |
| `SESSIONS` | Path to `sessions.csv` |
| `EVENTS_HMM` | Optional HMM-labeled events |
| `EVENT_COLUMNS` | Per-session event count columns expected from step01 |
| `REQUIRED_SESSION_COLUMNS` | Must exist or rebuild / error |
| `USER_FEATURE_COLUMNS` | Preferred order of cookie-level features (step05 depends on these names) |

### Objects created while running

| Name | What it is |
|------|------------|
| `sessions` | Raw visits from step01 |
| `frame` | Enriched session table |
| `hmm_shares` | Per-session mode mix (or `None`) |
| `work` | Behavior sessions only (`n_behavior_events > 0`) |
| `features` / `users` | One row per cookie |
| `stage` / `device` / `event_totals` | Intermediate rollups |

### Key session columns added

| Column | Meaning |
|--------|---------|
| `prior_sessions` | How many visits this cookie already had |
| `days_since_first_session` | Tenure at this visit |
| `start_hour` / `start_dow` / `is_weekend` | Timing |
| `deep_session` / `intent_session` / `engaged_or_deeper` | Depth flags |
| `hmm_share_*` / `hmm_dominant_mode` | Optional mode mix |

### Key user columns

| Column | Meaning |
|--------|---------|
| `n_sessions` | Visit frequency |
| `mean_duration_sec` / `mean_behavior_events` / `mean_content` | Typical activity |
| `mean_furthest_rank` | Typical depth |
| `share_deep` / `share_intent` / … | Mix of visit depths |
| `*_rate` | Share of behavior volume for that event |
| `conversion_rate` | Share of visits that convert |
| `share_desktop` / `mobile` / `tablet` | Device mix |
| `n_devices` / `n_referrers` | Diversity |
| `days_active` / `recency_days` | Span and freshness |

---

## Deep code walkthrough (every function)

### `load_sessions()`

**Job:** Get the visit table.

1. Read `sessions.csv`, or rebuild via step01 helpers.  
2. Require `REQUIRED_SESSION_COLUMNS`.  
3. Parse datetimes; coerce `converted` / `already_converted` with `_as_bool` (CSV may store `"True"` / `"1"`).

**Returns:** Sessions DataFrame.

---

### `_as_bool(series)`

**Job:** Robust boolean parse for CSV quirks (`true`/`1`/`yes`… → True).

---

### `enrich_session_features(sessions)`

**Job:** Add visit-level features used downstream and as rollup source.

**Steps:**

1. Ensure event count columns exist (0 if missing); coerce numerics.  
2. Per cookie: `prior_sessions`, `days_since_first_session`.  
3. Timing: hour, day-of-week, weekend flag.  
4. Depth flags from `furthest_stage` / `furthest_rank`.  
5. Optionally merge `_hmm_session_shares()` on `session_idx`.

**Returns:** Enriched session frame.

---

### `_hmm_session_shares()`

**Job:** Optional mode mix from step03.

1. If `sessionized_events_hmm.csv` missing → `None`.  
2. Drop conversions and blank modes.  
3. Count modes per session → row-normalize to shares.  
4. Rename to `hmm_share_<mode>`; add `hmm_dominant_mode`.

**Returns:** Share table or `None`.

---

### `user_features(sessions)`

**Job:** One habit vector per cookie.

**Steps:**

1. Keep sessions with at least one behavior event.  
2. Aggregate means/sums: sessions, duration, depth, conversion, devices, referrers, first/last visit.  
3. Stage mix → `share_deep`, `share_intent`, …  
4. Event totals / behavior sum → `page_view_rate`, `checkout_start_rate`, …  
5. Device mix → `share_desktop`, …  
6. `days_active`, `recency_days` vs latest snapshot.  
7. If present, average `hmm_share_*` across sessions.  
8. Order columns: `anonymous_id` + `USER_FEATURE_COLUMNS` + extras.

**Returns:** User feature DataFrame (input to step05).

---

### `main()`

```text
sessions = enrich_session_features(load_sessions())
users    = user_features(sessions)
write session_features.csv + user_features.csv
print means / conversion / whether HMM shares were included
```

---

## Acceptance checks

- One row per `session_id` in `session_features.csv`  
- One row per `anonymous_id` in `user_features.csv`  
- Names in `USER_FEATURE_COLUMNS` present for step05  

## Teaching takeaway

Answer: *“What does this cookie’s habit look like over time?”* — the bridge from visits/modes to audience clustering.
