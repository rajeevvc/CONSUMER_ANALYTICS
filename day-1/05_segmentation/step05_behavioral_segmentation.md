# Learner guide — Behavioral segmentation (`step05_behavioral_segmentation.py`)

## Goal (in plain English)

You already have **one scorecard per cookie** from step04 (`user_features.csv`).

This step asks: **“Which group of similar readers does each cookie belong to?”**

Two answers are produced side by side:

| Method | Plain meaning |
|--------|----------------|
| **K-Means** | Put every reader in **exactly one** bucket |
| **GMM** | Soft mixture model; we still assign the **most likely** bucket |

Marketing can then say “this person looks like a *bouncer*” vs “*converter*” and treat them differently.

## How to run

```bash
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

---

## Big picture (intuition)

Imagine each reader as a point on a map made from their habits (how often they visit, how deep they go, how often they convert, …).

1. **Scale** the map so “seconds” and “rates” use the same units.  
2. Try several numbers of groups (**k = 3…8**) and pick the split that looks cleanest (**silhouette**).  
3. Draw the groups with **K-Means** and again with **GMM**.  
4. Give each group a **human name** from its average behavior.  
5. Write a **profile table** (size, depth, conversion) so marketers can read it.

```text
user_features.csv
        │
        ▼
 load_user_features()          ← one row per cookie
        │
        ▼
 fit_segmentation()            ← scale → choose k → K-Means + GMM → name → profile
        │
        ▼
 save_segmentation()           ← CSVs + metrics JSON
```

---

## High-level variables (what they mean)

### Path / config constants

| Name | What it is |
|------|------------|
| `DAY1` | Folder `day-1/` (parent of `05_segmentation/`) |
| `OUTPUT` | `day-1/output/` where results are written |
| `USER_FEATURES` | Path to `user_features.csv` from step04 |
| `FEATURE_COLUMNS` | Ordered list of **numeric** columns used for clustering (must match step04 names) |
| `K_CANDIDATES` | `range(3, 9)` → try 3, 4, 5, 6, 7, or 8 groups |
| `SEED` | `42` — fixed random seed so runs are repeatable |

`anonymous_id` is the **reader key**. It is **not** put into the clustering matrix (IDs are labels, not behavior).

### Feature columns (the “map axes”)

These describe *how a cookie behaves over time*:

| Column | Intuition |
|--------|-----------|
| `n_sessions` | How often they come back |
| `mean_duration_sec` | How long a typical visit lasts |
| `mean_behavior_events` | How busy a typical visit is |
| `mean_content` | How much content they touch |
| `mean_furthest_rank` | How deep they usually get (1=landing … 5=deep) |
| `share_deep` / `share_intent` / `share_engaged` / `share_landing_or_scroll` | Mix of visit depths |
| `*_rate` columns | Share of sessions with that event (page view, scroll, paywall, checkout, …) |
| `conversion_rate` | Share of sessions that convert |

### Objects created while fitting

| Name | What it is |
|------|------------|
| `features` | DataFrame: one row per cookie + all feature columns |
| `matrix` | Raw numeric array used for clustering (`rows = cookies`, `cols = FEATURE_COLUMNS`) |
| `scaler` | `StandardScaler` — learns mean/std of each column |
| `scaled` | Same matrix after standardization (fair distances) |
| `k` | Chosen number of clusters / mixture components |
| `k_scores` | List of `{k, silhouette}` tried during selection |
| `kmeans` / `gmm` | Fitted model objects |
| `kmeans_labels` / `gmm_labels` | Integer group id per cookie (0…k−1) |
| `labeled` | `features` plus segment ids and human labels |
| `profiles` | Dict of summary tables keyed by `"kmeans"` / `"gmm"` |
| `metrics` | Quality numbers written to JSON |
| `result` | `{"audience", "profiles", "metrics"}` returned by `fit_segmentation` |

### Columns added on the audience table

| Column | Meaning |
|--------|---------|
| `kmeans_segment` | Integer cluster id from K-Means |
| `gmm_segment` | Integer component id from GMM |
| `kmeans_label` | Friendly name (e.g. `bouncers`) |
| `gmm_label` | Friendly name for the GMM assignment |

---

## Deep code walkthrough (every function)

### Bootstrap (top of file)

Sets paths, imports sklearn models, and defines `FEATURE_COLUMNS`.

Also adds `04_feature_engineering` to `sys.path` so this script can **rebuild** user features if the CSV is missing (by importing step04 helpers).

---

### `load_user_features()`

**Job:** Get a clean table of one row per cookie.

**Steps:**

1. If `user_features.csv` exists → read it.  
2. Else → rebuild: `load_sessions()` → `enrich_session_features()` → `user_features()` from step04.  
3. Pass the table through `_ensure_feature_columns()`.

**Returns:** `features` DataFrame ready for clustering.

---

### `_ensure_feature_columns(features)`

**Job:** Sanity-check and tidy the feature table so clustering does not blow up.

**Steps:**

1. Require `anonymous_id`.  
2. Require every name in `FEATURE_COLUMNS` (if missing → tell you to re-run step04).  
3. Convert feature columns to numbers; replace blanks with `0`.  
4. **Cap** `mean_duration_sec` at the **99.5th percentile** — a few marathon sessions should not stretch the map and pull clusters.  
5. Drop rows with no `anonymous_id`; reset the index.

**Returns:** Cleaned `features` copy.

---

### `fit_segmentation(features, seed=SEED)`

**Job:** End-to-end clustering: scale → choose k → fit both models → name segments → scorecards → metrics.

**Steps:**

1. Build `matrix` from `FEATURE_COLUMNS`.  
2. Replace any non-finite values with 0 (`nan_to_num`).  
3. Fit `StandardScaler` → `scaled`.  
   - *Why?* Without this, `mean_duration_sec` (thousands) would drown `conversion_rate` (0–1).  
4. Call `_choose_k(scaled)` → best `k` and the trial scoreboard.  
5. Fit **K-Means** with that `k` → `kmeans_labels`.  
6. Fit **GMM** with the same `k` → `gmm_labels`.  
7. Copy features into `labeled`; attach both label columns.  
8. `_name_segments(...)` for K-Means and GMM → map ids to words.  
9. `_profile_table(...)` twice → marketing scorecards.  
10. Pack `metrics` (readers, inertia, silhouette, BIC/AIC, k-selection).  

**Returns:**

```python
{
  "audience": labeled,      # every cookie + segment columns
  "profiles": {...},        # summary tables
  "metrics": {...},         # quality numbers
}
```

---

### `_choose_k(scaled, seed)`

**Job:** Pick how many groups to use.

**Intuition:** Too few groups = everyone looks the same. Too many = marketing cannot act. We try 3–8 and keep the best **silhouette** (higher = tighter, better-separated blobs).

**Steps:**

1. Take a random sample of up to **12,000** rows (faster on big audiences).  
2. For each `k` in `K_CANDIDATES`, run K-Means and compute silhouette.  
3. Pick the `k` with the highest silhouette.

**Returns:** `(best_k, list_of_scores)`.

---

### `_safe_silhouette(scaled, labels)`

**Job:** Measure cluster quality without crashing on edge cases.

**Steps:**

1. Need at least 2 rows and 2 distinct labels — else return `None`.  
2. If more than **20,000** rows, score a random subsample (silhouette is expensive).  
3. Return silhouette rounded to 4 decimals.

Used for both K-Means and GMM final metrics.

---

### `_name_segments(frame, segment_column)`

**Job:** Turn cold integers (`0`, `1`, `2`…) into names a marketer understands.

**How:** For each segment, look at averages:

| If the group looks like… | Name |
|--------------------------|------|
| conversion_rate ≥ 3% | `converters` |
| mean depth ≥ 4.5 | `deep_checkout` |
| depth ≥ 3.8 and often views plans | `intent_engaged` |
| depth ≥ 3.0 | `regular_readers` |
| many sessions but shallow | `repeat_browsers` |
| depth ≤ 1.5 | `bouncers` |
| anything else | `casual_browsers` |

Depth ranks in this lab: landing=1 → scroll=2 → engaged=3 → intent=4 → deep=5.

If two groups get the same base name, add `_2`, `_3`, …

**Returns:** `{segment_id: "friendly_name", ...}`

---

### `_profile_table(frame, segment_column, label_column)`

**Job:** Build the one-page scorecard per segment.

For each group, compute:

| Field | Meaning |
|-------|---------|
| `segment` | Integer id |
| `label` | Friendly name |
| `readers` | How many cookies |
| `share_of_readers` | % of audience |
| `mean_sessions` / `mean_duration_sec` / `mean_behavior_events` | Activity level |
| `mean_furthest_rank` | Typical depth |
| `conversion_rate` | How often they convert |
| `share_deep` / `share_intent` / `subscription_view_rate` | Intent / monetization signals |

Sorted largest segment first.

**Returns:** A small DataFrame — one row per segment.

---

### `save_segmentation(result)`

**Job:** Persist results under `day-1/output/`.

**Writes:**

1. `audience_segments.csv` — selected columns per cookie (ids + key features + both segment assignments).  
2. `segment_profiles_kmeans.csv` / `segment_profiles_gmm.csv` — the scorecards.  
3. `segmentation_metrics.json` — k, silhouette, BIC/AIC, feature list.

Also deletes an old `segment_profiles_hdbscan.csv` if present (HDBSCAN is no longer in the teaching path).

---

### `main()`

**Job:** Glue the pipeline and print a short human summary.

```text
print banner
features = load_user_features()
result   = fit_segmentation(features)
save_segmentation(result)
print reader count, k, silhouettes, BIC
print both profile tables
print output folder
```

`if __name__ == "__main__": main()` means: running this file as a script starts `main()`; importing it does not.

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
| Question | How are they reading **now**? | Who are they as an **audience**? |
