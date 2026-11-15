# Day 1 — Consumer / Media Behavioral Analytics Lab

Lean learner guides for each implementation. Work **in order**.

## Environment

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

Raw data lives in `day-1/data/`. Outputs go to `day-1/output/`.

## Pipeline order

| Step | Script | Learner guide |
|------|--------|----------------|
| 1 | `sessionize.py` | [README_01_sessionize.md](README_01_sessionize.md) |
| 1b (optional) | `sessionize_duckdb_sql.py` | [README_01b_sessionize_duckdb.md](README_01b_sessionize_duckdb.md) |
| 2 | `journey_analysis.py` | [README_02_journey_analysis.md](README_02_journey_analysis.md) |
| 3 | `behavioral_state_modeling.py` | [README_03_behavioral_state_modeling.md](README_03_behavioral_state_modeling.md) |
| 4 | `feature_engineering.py` | [README_04_feature_engineering.md](README_04_feature_engineering.md) |
| 5 | `behavioral_segmentation.py` | [README_05_behavioral_segmentation.md](README_05_behavioral_segmentation.md) |

## Full run (CSV path)

```bash
python day-1/sessionize.py
python day-1/journey_analysis.py
python day-1/behavioral_state_modeling.py   # optional but recommended before features
python day-1/feature_engineering.py
python day-1/behavioral_segmentation.py
```

## Concepts to keep straight

| Term | Meaning in this lab |
|------|---------------------|
| Cookie (`anonymous_id`) | Long-lived browser / visitor ID |
| Session (`session_id`) | One visit; new session after **30 min** idle |
| Stage tags | `landing → scroll → engaged → intent → deep` (+ registration / subscription) |
| Conversion | `register_complete` or `subscription_active` within 7 days |

## What each step achieves

1. **Sessionize** — cut clickstream into visits; label conversion  
2. **Journey** — Funnel + Markov + DFG on visits  
3. **HMM** — latent reading modes inside sequences  
4. **Features** — session → user vectors  
5. **Segmentation** — cluster cookies (K-Means + GMM)  
