# Day 1 algorithm examples

Toy demos ordered by **learning sequence**.

```
examples/
  _shared/                 toy raw events + toy sessionized events
  01_sessionize/           30-minute inactivity sessions
  02_journey/              Funnel → Markov → DFG
  03_state_modeling/       HMM latent modes
  04_feature_engineering/  session → user features
  05_segmentation/         K-Means + GMM
```

## Setup

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

## Run in learning order

```bash
# 1) Sessionize
python day-1/examples/01_sessionize/01_sessionize_example.py

# 2) Journey
python day-1/examples/02_journey/01_funnel_example.py
python day-1/examples/02_journey/02_markov_example.py
python day-1/examples/02_journey/03_dfg_example.py

# 3) State modeling
python day-1/examples/03_state_modeling/01_hmm_example.py

# 4) Features
python day-1/examples/04_feature_engineering/01_feature_engineering_example.py

# 5) Segmentation
python day-1/examples/05_segmentation/01_segmentation_example.py
```

These examples use **toy data** and do not need `day-1/data/web_events.csv`.  
Full lab scripts remain `step01`…`step05`.

## Where is the input?

The examples **do not** read `day-1/data/web_events.csv`. Inputs are defined **in code**:

| Example folder | Input location |
|----------------|----------------|
| `01_sessionize/` | `examples/_shared/toy_raw_events.py` → `load_raw_events()` (raw clicks, no session yet) |
| `02_journey/` | `examples/_shared/toy_sessions.py` → `load_toy_events()` (4 hand-built sessions) |
| `03_state_modeling/` | Same `toy_sessions.py` |
| `04_feature_engineering/` | Same `toy_sessions.py` |
| `05_segmentation/` | Built inside `05_segmentation/01_segmentation_example.py` → `toy_audience()` (12 synthetic cookies) |

- Raw toy clickstream: **`day-1/examples/_shared/toy_raw_events.py`**
- Sessionized toy journeys: **`day-1/examples/_shared/toy_sessions.py`**
- Full lab CSVs under `day-1/data/` are only for `step01`…`step05`, not these demos

## Map to lab steps

| Learning folder | Lab step | Algorithms |
|-----------------|----------|------------|
| `01_sessionize/` | `step01_sessionize.py` | 30-min inactivity, dedupe, furthest stage, 7-day label |
| `02_journey/` | `step02_journey_analysis.py` | Funnel, Markov, DFG |
| `03_state_modeling/` | `step03_behavioral_state_modeling.py` | Categorical HMM |
| `04_feature_engineering/` | `step04_feature_engineering.py` | Session → user rollup |
| `05_segmentation/` | `step05_behavioral_segmentation.py` | K-Means, GMM |

## Deep code walkthroughs

Each example `.py` has a paired `.md` that explains every function, input, and constant. Terminal output is kept simple: **RAW** input, then one **PROCESSED** result (see each walkthrough’s sample section).

| Code | Deep README |
|------|-------------|
| `_shared/` toy loaders | [`_shared/README.md`](_shared/README.md) |
| `01_sessionize/01_sessionize_example.py` | [`01_sessionize/01_sessionize_example.md`](01_sessionize/01_sessionize_example.md) |
| `02_journey/01_funnel_example.py` | [`02_journey/01_funnel_example.md`](02_journey/01_funnel_example.md) |
| `02_journey/02_markov_example.py` | [`02_journey/02_markov_example.md`](02_journey/02_markov_example.md) |
| `02_journey/03_dfg_example.py` | [`02_journey/03_dfg_example.md`](02_journey/03_dfg_example.md) |
| `03_state_modeling/01_hmm_example.py` | [`03_state_modeling/01_hmm_example.md`](03_state_modeling/01_hmm_example.md) |
| `04_feature_engineering/01_feature_engineering_example.py` | [`04_feature_engineering/01_feature_engineering_example.md`](04_feature_engineering/01_feature_engineering_example.md) |
| `05_segmentation/01_segmentation_example.py` | [`05_segmentation/01_segmentation_example.md`](05_segmentation/01_segmentation_example.md) |

## How they connect

```
Sessionize (step01)                 ← examples/01_sessionize
   → Journey: Funnel / Markov / DFG ← examples/02_journey
   → HMM                            ← examples/03_state_modeling
   → Feature engineering            ← examples/04_feature_engineering
   → Segmentation                   ← examples/05_segmentation
```
