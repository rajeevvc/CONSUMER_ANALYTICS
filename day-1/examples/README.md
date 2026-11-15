# Day 1 algorithm examples

Toy demos ordered by **learning sequence** (after sessionization).

```
examples/
  _shared/                 shared toy clickstream
  01_journey/              Funnel → Markov → DFG
  02_state_modeling/       HMM latent modes
  03_feature_engineering/  session → user features
  04_segmentation/         K-Means + GMM
```

## Setup

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

## Run in learning order

```bash
# 1) Journey
python day-1/examples/01_journey/01_funnel_example.py
python day-1/examples/01_journey/02_markov_example.py
python day-1/examples/01_journey/03_dfg_example.py

# 2) State modeling
python day-1/examples/02_state_modeling/01_hmm_example.py

# 3) Features
python day-1/examples/03_feature_engineering/01_feature_engineering_example.py

# 4) Segmentation
python day-1/examples/04_segmentation/01_segmentation_example.py
```

Lab prerequisite (full pipeline): `python day-1/step01_sessionize.py`  
These examples use **toy data** and do not need the full CSV.

## Where is the input?

The examples **do not** read `day-1/data/web_events.csv`. Inputs are defined **in code**:

| Example folder | Input location |
|----------------|----------------|
| `01_journey/` | `examples/_shared/toy_sessions.py` → `load_toy_events()` (4 hand-built sessions) |
| `02_state_modeling/` | Same `toy_sessions.py` |
| `03_feature_engineering/` | Same `toy_sessions.py` |
| `04_segmentation/` | Built inside `04_segmentation/01_segmentation_example.py` → `toy_audience()` (12 synthetic cookies) |

- Shared clickstream toy data: **`day-1/examples/_shared/toy_sessions.py`**
- Full lab CSVs under `day-1/data/` are only for `step01`…`step05`, not these demos

## Map to lab steps

| Learning folder | Lab step | Algorithms |
|-----------------|----------|------------|
| `01_journey/` | `step02_journey_analysis.py` | Funnel, Markov, DFG |
| `02_state_modeling/` | `step03_behavioral_state_modeling.py` | Categorical HMM |
| `03_feature_engineering/` | `step04_feature_engineering.py` | Session → user rollup |
| `04_segmentation/` | `step05_behavioral_segmentation.py` | K-Means, GMM |

## How they connect

```
Sessionize (step01)
   → Journey: Funnel / Markov / DFG     (observed paths)
   → HMM                                (latent modes)
   → Feature engineering                (cookie vectors)
   → Segmentation                       (audience groups)
```
