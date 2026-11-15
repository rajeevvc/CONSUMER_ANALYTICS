# Learner guide — Feature engineering (`step04_feature_engineering.py`)

## Goal

Build ML-ready tables:

1. **Session features** — enrich each visit  
2. **User features** — one vector per cookie (`anonymous_id`) for segmentation  

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

## Deep code walkthrough

### Bootstrap

`DAY1` / `OUTPUT` paths; `sys.path` includes `01_sessionize` so missing `sessions.csv` can be rebuilt.

`EVENT_COLUMNS` — behavior counts expected from step01.  
`USER_FEATURE_COLUMNS` — ordered list written for segmentation (step05 depends on these names).

---

### `load_sessions()`

1. Read `sessions.csv` or rebuild via step01 helpers.  
2. Require `REQUIRED_SESSION_COLUMNS`.  
3. Parse datetimes; coerce `converted` / `already_converted` with `_as_bool` (handles CSV `"True"`/`"1"`).

---

### `enrich_session_features(sessions)`

Session-grain enrichments used downstream and as rollup source:

| Addition | Meaning |
|----------|---------|
| Fill missing event count cols | zeros if absent |
| `prior_sessions` | cumcount of sessions per cookie |
| `days_since_first_session` | tenure at this visit |
| `start_hour`, `start_dow`, `is_weekend` | timing |
| `deep_session`, `intent_session`, `engaged_or_deeper` | depth flags |
| Optional `hmm_share_*` | from `_hmm_session_shares()` |

#### `_hmm_session_shares()`

If `sessionized_events_hmm.csv` exists:

1. Drop conversions / empty modes.  
2. Count modes per session → row-normalize to shares.  
3. Rename columns `hmm_share_<mode>`; add `hmm_dominant_mode`.  

If the file is missing, enrichment simply skips HMM columns.

---

### `user_features(sessions)`

Filter to sessions with `n_behavior_events > 0`, then group by `anonymous_id`:

**Aggregates**

- Frequency: `n_sessions`, `days_active`  
- Engagement: mean duration / events / content / furthest rank  
- Outcome: `conversion_rate`, `ever_converted`  
- Devices/referrers: uniqueness counts  

**Stage shares** from furthest-stage distribution:

`share_deep`, `share_intent`, `share_engaged`, `share_landing_or_scroll`

**Event rates**

```text
page_view_rate = sum(page_view) / sum(n_behavior_events)   (etc.)
```

**Device shares** desktop/mobile/tablet.

**Recency**

```text
recency_days = (global max last_session − this cookie's last_session) in days
```

**Optional** mean of any `hmm_share_*` columns.

Returns columns ordered: `anonymous_id` + `USER_FEATURE_COLUMNS` + extras.

---

### `main()`

```text
load_sessions → enrich_session_features → user_features
             → write session_features.csv + user_features.csv
             → print summary stats
```

---

## Acceptance checks

- `# users` ≈ distinct cookies with behavior sessions  
- Segmentation feature columns present on `user_features.csv`  
- Rates between 0 and 1  

## Teaching takeaway

Bridge from **visits** → **visitor feature vectors** for clustering.
