# Learner guide — Behavioral segmentation (`step05_behavioral_segmentation.py`)

## Goal

Cluster **cookies** into audience segments using user-level features.

- **K-Means** — hard clusters  
- **GMM** — soft mixture; label = argmax component  

## How to run

```bash
conda activate awsproject
python day-1/04_feature_engineering/step04_feature_engineering.py
python day-1/05_segmentation/step05_behavioral_segmentation.py
```

### Tiny worked example

```bash
python day-1/05_segmentation/examples/01_segmentation_example.py
```

## Input / Output

| Input | `day-1/output/user_features.csv` |
|-------|-----------------------------------|
| Outputs | `audience_segments.csv`, `segment_profiles_kmeans.csv`, `segment_profiles_gmm.csv`, `segmentation_metrics.json` |

### Feature columns used for clustering

`n_sessions`, `mean_duration_sec`, `mean_behavior_events`, `mean_content`,  
`mean_furthest_rank`, `share_deep`, `share_intent`, `share_engaged`,  
`share_landing_or_scroll`, event rates, `conversion_rate`

`anonymous_id` is the key (not a numeric feature).

---

## Deep code walkthrough

### Bootstrap

Paths to `OUTPUT` / `user_features.csv`; `sys.path` adds `04_feature_engineering` for rebuild.

`FEATURE_COLUMNS` must match step04 names. `K_CANDIDATES = range(3, 9)`, `SEED = 42`.

---

### `load_user_features()` / `_ensure_feature_columns()`

1. Read CSV or rebuild via step04 (`enrich_session_features` + `user_features`).  
2. Require every `FEATURE_COLUMNS` entry.  
3. Coerce numerics; fill NaN with 0.  
4. Cap `mean_duration_sec` at the 99.5th percentile so a few marathon sessions do not dominate distance.

---

### `fit_segmentation(features)`

1. Build matrix from `FEATURE_COLUMNS`; `nan_to_num` safety.  
2. `StandardScaler` — seconds and rates become comparable.  
3. `_choose_k` — for k in 3…8, K-Means on a ≤12k sample; pick max silhouette.  
4. Fit **K-Means** and **GMM** (`covariance_type="full"`, `n_init=3`) at that k.  
5. `_name_segments` for both label columns.  
6. `_profile_table` per method.  
7. Pack metrics: inertia, silhouette, BIC/AIC, k-selection table.

#### `_choose_k`

Silhouette on a random sample keeps selection affordable on large audiences.

#### `_safe_silhouette`

Returns `None` if fewer than 2 clusters; may subsample to 20k rows for speed.

#### `_name_segments` (heuristics)

| Condition | Label |
|-----------|--------|
| `conversion_rate ≥ 0.03` | `converters` |
| `mean_furthest_rank ≥ 4.5` | `deep_checkout` |
| depth ≥ 3.8 and plan-view rate ≥ 0.08 | `intent_engaged` |
| depth ≥ 3.0 | `regular_readers` |
| many sessions but shallow | `repeat_browsers` |
| depth ≤ 1.5 | `bouncers` |
| else | `casual_browsers` |

Duplicate names get `_2`, `_3`, … suffixes.

#### `_profile_table`

Segment scorecard: size, share, mean sessions/duration/depth, conversion, intent/deep rates.

---

### `save_segmentation(result)`

Writes audience assignments (selected columns), both profile CSVs, metrics JSON. Deletes stale `segment_profiles_hdbscan.csv` if present (HDBSCAN removed from the teaching path).

---

### `main()`

```text
load_user_features → fit_segmentation → save_segmentation → print profiles
```

---

## Acceptance checks

- One row per cookie in `audience_segments.csv`  
- Profile `readers` sum ≈ total cookies  
- Metrics JSON includes both `kmeans` and `gmm`  

## Teaching takeaway

Answer: *“What kind of audience is this visitor over time?”*

| | HMM (step03) | Segmentation (step05) |
|--|--------------|------------------------|
| Grain | Event / latent mode | Cookie / segment |
| Input | Sessionized events | User features |
| Question | How are they reading now? | Who are they as an audience? |
