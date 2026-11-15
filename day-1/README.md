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
| 1 | `step01_sessionize.py` | [step01_sessionize.md](step01_sessionize.md) |
| 1b (optional) | `step01b_sessionize_duckdb_sql.py` | [step01b_sessionize_duckdb.md](step01b_sessionize_duckdb.md) |
| 2 | `step02_journey_analysis.py` | [step02_journey_analysis.md](step02_journey_analysis.md) · [examples/01_journey](examples/01_journey/) |
| 3 | `step03_behavioral_state_modeling.py` | [step03_behavioral_state_modeling.md](step03_behavioral_state_modeling.md) · [examples/02_state_modeling](examples/02_state_modeling/) |
| 4 | `step04_feature_engineering.py` | [step04_feature_engineering.md](step04_feature_engineering.md) · [examples/03_feature_engineering](examples/03_feature_engineering/) |
| 5 | `step05_behavioral_segmentation.py` | [step05_behavioral_segmentation.md](step05_behavioral_segmentation.md) · [examples/04_segmentation](examples/04_segmentation/) |

## Full run (CSV path)

```bash
python day-1/step01_sessionize.py
python day-1/step02_journey_analysis.py
python day-1/step03_behavioral_state_modeling.py   # optional but recommended before features
python day-1/step04_feature_engineering.py
python day-1/step05_behavioral_segmentation.py
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
