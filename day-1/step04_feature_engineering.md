# Learner guide — Feature engineering (`step04_feature_engineering.py`)

## Goal

Build ML-ready tables:

1. **Session features** — enrich each visit  
2. **User features** — one vector per cookie (`anonymous_id`) for segmentation  

Sessionize gives visit summaries; this step rolls them up to **audience-level** features (frequency, recency, engagement rates).

## How to run

```bash
conda activate awsproject
python day-1/step01_sessionize.py
python day-1/step03_behavioral_state_modeling.py   # optional — adds hmm_share_* if present
python day-1/step04_feature_engineering.py
```

### Tiny worked example

```bash
python day-1/examples/05_feature_engineering_example.py
```

See [examples/README.md](examples/README.md).

## Input

| File | Role |
|------|------|
| `day-1/output/sessions.csv` | **Required** |
| `day-1/output/sessionized_events_hmm.csv` | Optional — HMM mode shares per session |

### Expected session columns (minimum)

`session_idx`, `session_id`, `anonymous_id`, `session_start`, `session_end`,  
`device_type`, `referrer`, `n_behavior_events`, `n_content`,  
`furthest_rank`, `furthest_stage`, `duration_sec`,  
`converted`, `already_converted`, plus behavior event count columns.

## What you must implement

### Session enrich
- Ensure event count columns exist  
- Flags such as `deep_session`, `intent_session`, `engaged_or_deeper`  
- Optional: merge `hmm_share_*` from HMM output  

### User rollup (one row per `anonymous_id`)
From sessions with behavior events:
- **Frequency** — `n_sessions`, `days_active`  
- **Recency** — `recency_days` from last session vs snapshot  
- **Engagement** — mean duration, mean behavior events, mean furthest rank  
- **Stage shares** — `share_landing_or_scroll`, `share_engaged`, `share_intent`, `share_deep`  
- **Event rates** — e.g. `page_view_rate`, `subscription_view_rate`, … = count / behavior events  
- **Devices** — share desktop/mobile/tablet  
- **Outcome** — `conversion_rate`  
- Optional mean `hmm_share_*`  

## Output

| File | Grain |
|------|--------|
| `day-1/output/session_features.csv` | One row per session |
| `day-1/output/user_features.csv` | One row per cookie |

## Acceptance checks

- `# users` ≈ distinct cookies with behavior sessions  
- Every segmentation feature column present on `user_features.csv`  
- Rates are between 0 and 1  

## Teaching takeaway

Bridge from **visits** → **visitor feature vectors** for clustering.
