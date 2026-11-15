# CONSUMER_ANALYTICS

Hands-on lab for **anonymous consumer / media behavioral analytics**.

Start with clickstreams, build visits, map journeys, learn latent modes, engineer user features, and segment audiences — without relying on PII.

## What’s in this repo

| Path | Role |
|------|------|
| [`day-1/`](day-1/) | Full Day 1 lab (scripts, guides, toy examples, data stubs) |
| [`.gitignore`](.gitignore) | Keeps large CSVs / `output/` / sibling trees out of git |

Day 1 is organized **by pipeline context**. Each step folder holds the lab script, learner guide, and toy examples together.

```
CONSUMER_ANALYTICS/
├── README.md                 ← this file
├── .gitignore
└── day-1/
    ├── README.md             ← Day 1 run order & concepts
    ├── _paths.py             ← shared data/output path helper
    ├── _shared/              ← toy inputs for examples (in code)
    ├── data/                 ← raw tables (large CSVs local-only)
    ├── output/               ← pipeline results (gitignored)
    ├── 01_sessionize/
    ├── 02_journey/
    ├── 03_state_modeling/
    ├── 04_feature_engineering/
    └── 05_segmentation/
```

## Day 1 pipeline (learning order)

```
Raw clicks
  → 01 Sessionize          visits + conversion label
  → 02 Journey             Funnel / Markov / DFG
  → 03 State modeling      Categorical HMM modes
  → 04 Feature engineering session → user vectors
  → 05 Segmentation        K-Means + GMM audiences
```

| Step | Folder | What it does |
|------|--------|----------------|
| 1 | [`day-1/01_sessionize/`](day-1/01_sessionize/) | 30-min inactivity sessions, dedupe, furthest stage, 7-day conversion |
| 1b | same | Optional DuckDB/SQL sessionize path |
| 2 | [`day-1/02_journey/`](day-1/02_journey/) | Funnel reach/advance, Markov (+ exit), DFG process map |
| 3 | [`day-1/03_state_modeling/`](day-1/03_state_modeling/) | Latent reading modes (HMM) |
| 4 | [`day-1/04_feature_engineering/`](day-1/04_feature_engineering/) | Session → cookie feature vectors |
| 5 | [`day-1/05_segmentation/`](day-1/05_segmentation/) | Audience clusters (K-Means + GMM) |

Inside each context folder:

- `step0N_*.py` — full lab on `day-1/data` → writes `day-1/output`
- `step0N_*.md` — lean learner guide
- `examples/` — toy demos that print **RAW** then **PROCESSED**
- `README.md` — short folder index

Shared toy loaders for examples: [`day-1/_shared/`](day-1/_shared/).

## Quick start

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

### Full lab (needs local data under `day-1/data/`)

```bash
python day-1/01_sessionize/step01_sessionize.py
python day-1/02_journey/step02_journey_analysis.py
python day-1/03_state_modeling/step03_behavioral_state_modeling.py
python day-1/04_feature_engineering/step04_feature_engineering.py
python day-1/05_segmentation/step05_behavioral_segmentation.py
```

### Toy examples (no large CSV required)

```bash
python day-1/01_sessionize/examples/01_sessionize_example.py
python day-1/02_journey/examples/01_funnel_example.py
python day-1/02_journey/examples/02_markov_example.py
python day-1/02_journey/examples/03_dfg_example.py
python day-1/03_state_modeling/examples/01_hmm_example.py
python day-1/04_feature_engineering/examples/01_feature_engineering_example.py
python day-1/05_segmentation/examples/01_segmentation_example.py
```

Details, inputs/outputs, and concepts: **[`day-1/README.md`](day-1/README.md)**.

## Key terms

| Term | Meaning |
|------|---------|
| Cookie (`anonymous_id`) | Long-lived visitor ID |
| Session (`session_id`) | One visit; new session after **30 minutes** idle |
| Stage tags | `landing → scroll → engaged → intent → deep` (+ registration / subscription) |
| Conversion | `register_complete` or `subscription_active` within 7 days |

## Data & git notes

- **Tracked:** Day 1 scripts, guides, examples, small catalog/subscription samples, docs  
- **Not tracked (local):** `day-1/output/`, oversized `web_events.csv` / `app_events.csv` / parquet extracts  
- Place or regenerate large clickstream files under `day-1/data/` before running the full lab  

See [`day-1/data/README.md`](day-1/data/README.md) for table inventory.
