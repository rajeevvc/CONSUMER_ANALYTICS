# Day 1 — Consumer / Media Behavioral Analytics Lab

Lean learner guides for each implementation. Work **in order**.

## Environment

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

Raw data lives in `day-1/data/`. Outputs go to `day-1/output/`.

## Folder layout (by context)

```
day-1/
  data/                      raw tables
  output/                    pipeline CSVs
  _shared/                   toy inputs for examples
  01_sessionize/             lab + toy example
  02_journey/                lab + Funnel / Markov / DFG examples
  03_state_modeling/         lab + HMM example
  04_feature_engineering/    lab + features example
  05_segmentation/           lab + segmentation example
```

Each context folder holds:

- `step0N_*.py` — full lab script  
- `step0N_*.md` — learner guide **with deep code walkthrough** (functions, constants, pipeline)  
- `examples/` — toy demos (RAW → PROCESSED)  
- `README.md` — short folder index

## Pipeline order

| Step | Context folder | Script | Learner guide |
|------|----------------|--------|----------------|
| 1 | [`01_sessionize/`](01_sessionize/) | `step01_sessionize.py` | [guide](01_sessionize/step01_sessionize.md) · [example](01_sessionize/examples/) |
| 1b | same | `step01b_sessionize_duckdb_sql.py` | [guide](01_sessionize/step01b_sessionize_duckdb.md) |
| 2 | [`02_journey/`](02_journey/) | `step02_journey_analysis.py` | [guide](02_journey/step02_journey_analysis.md) · [examples](02_journey/examples/) |
| 3 | [`03_state_modeling/`](03_state_modeling/) | `step03_behavioral_state_modeling.py` | [guide](03_state_modeling/step03_behavioral_state_modeling.md) · [example](03_state_modeling/examples/) |
| 4 | [`04_feature_engineering/`](04_feature_engineering/) | `step04_feature_engineering.py` | [guide](04_feature_engineering/step04_feature_engineering.md) · [example](04_feature_engineering/examples/) |
| 5 | [`05_segmentation/`](05_segmentation/) | `step05_behavioral_segmentation.py` | [guide](05_segmentation/step05_behavioral_segmentation.md) · [example](05_segmentation/examples/) |

## Full run (CSV path)

```bash
python day-1/01_sessionize/step01_sessionize.py
python day-1/02_journey/step02_journey_analysis.py
python day-1/03_state_modeling/step03_behavioral_state_modeling.py   # optional but recommended before features
python day-1/04_feature_engineering/step04_feature_engineering.py
python day-1/05_segmentation/step05_behavioral_segmentation.py
```

## Toy examples (learning order)

```bash
python day-1/01_sessionize/examples/01_sessionize_example.py
python day-1/02_journey/examples/01_funnel_example.py
python day-1/02_journey/examples/02_markov_example.py
python day-1/02_journey/examples/03_dfg_example.py
python day-1/03_state_modeling/examples/01_hmm_example.py
python day-1/04_feature_engineering/examples/01_feature_engineering_example.py
python day-1/05_segmentation/examples/01_segmentation_example.py
```

Toy inputs live in [`_shared/`](_shared/). Examples do **not** need `data/web_events.csv`.

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
