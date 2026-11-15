# `01_segmentation_example.py` — deep code walkthrough

**Question:** Which audience group does each cookie belong to?

**Maps to lab:** `day-1/05_segmentation/step05_behavioral_segmentation.py`

**Run:**

```bash
conda activate awsproject
python day-1/05_segmentation/examples/01_segmentation_example.py
```

---

## Why this exists

After feature engineering, each cookie is a numeric vector. **Segmentation** groups similar vectors into audiences:

- **K-Means** — hard assignment to nearest centroid  
- **GMM** — soft mixture of Gaussians; we take `argmax` for a hard label  

This toy builds a **synthetic 12-cookie audience** (clearer than the 4 single-session journey toys) with three planted personas.

---

## Feature columns used for fitting

```python
FEATURE_COLUMNS = [
    "n_sessions",
    "mean_duration_sec",
    "mean_furthest_rank",
    "share_intent",
    "share_deep",
    "subscription_view_rate",
    "conversion_rate",
]
```

`persona` is **ground truth for teaching only** — it is never passed into the scaler / clusterers.

---

## Function 1: `toy_audience()`

Creates 12 rows:

| Group | IDs | Design |
|-------|-----|--------|
| Bouncers | B1–B4 | shallow depth 1.0, short duration, no convert |
| Readers | R1–R4 | mid depth ~3+, longer duration, no convert |
| Converters | C1–C4 | deep depth ~4.5+, high intent/deep rates, convert |

Slight within-group noise (duration/depth increments) so clustering isn’t trivial equality.

---

## Function 2: `name_segment(part)`

After clustering, numeric ids are renamed from **profile means**:

```
if mean conversion_rate ≥ 0.2 → "converters"
else if mean furthest_rank ≥ 2.5 → "regular_readers"
else → "bouncers"
```

Threshold `2.5` is intentional: mid-depth readers sit above it; pure landing bouncers sit below.

---

## Function 3: `fit_segmentation(users)` — full pipeline

### 1) Scale

```python
scaled = StandardScaler().fit_transform(matrix)
```

Seconds and rates live on different scales; without scaling, duration would dominate distance.

### 2) Choose `k` with silhouette

Try `k = 2, 3, 4` with K-Means (`n_init=10`, `random_state=42`). Pick the `k` with highest silhouette score.

On this designed toy, **`k = 3`** wins.

### 3) Fit both models at `best_k`

- `KMeans` → `kmeans_segment` (0…k-1)
- `GaussianMixture(covariance_type="full", n_init=3)` → `gmm_segment`

### 4) Name segments

Map each numeric segment through `name_segment`. `unique_map` appends `_2`, `_3`, … if two clusters would get the same name (safety).

### 5) Store diagnostics on `DataFrame.attrs`

| Attr | Meaning |
|------|---------|
| `k` | Chosen cluster count |
| `silhouette_scores` | List of `(k, score)` tuples |
| `gmm_bic` | GMM BIC on scaled data (lower often better when comparing GMMs) |

---

## Function 4: `profile(frame, segment_col, label_col)`

One summary row per segment: size, mean depth, mean conversion, mean `share_deep`. Used to read “what is this audience like?”

---

## What `main()` prints

| Block | Content |
|-------|---------|
| **RAW** | Toy audience feature table |
| **PROCESSED** | Segment assignment per cookie |

---

## K-Means vs GMM (teaching contrast)

| | K-Means | GMM |
|-|---------|-----|
| Assignment | Hard nearest centroid | Soft responsibilities → argmax |
| Shape assumption | Spherical-ish clusters in scaled space | Full covariance ellipses (`full`) |
| Extra metric here | Silhouette for k | BIC stored for model quality |

On this clean toy they usually recover the same three groups.

---

## Lab connection

`step05` runs the same scale → choose k → K-Means + GMM flow on **real user features** from `step04` (often more columns). Naming rules may be richer; HDBSCAN was removed from the teaching path.

## Sample terminal output (what you see when you run it)

### RAW — toy audience features

```text
anonymous_id         persona  mean_furthest_rank  conversion_rate  share_deep
          B1   bouncer_truth                 1.0              0.0         0.0
          …
          R1    reader_truth                 3.0              0.0         0.0
          …
          C1 converter_truth                 4.5              0.4         0.3
```

**How to read it:** 12 cookies with planted personas (not used for fitting).

### PROCESSED — segment assignments

```text
anonymous_id         persona    kmeans_label       gmm_label
          B1   bouncer_truth        bouncers        bouncers
          …
          R1    reader_truth regular_readers regular_readers
          …
          C1 converter_truth      converters      converters

Note: chosen k=3; toy recovers bouncers / regular_readers / converters.
```

**How to read it:** Each cookie gets a named segment. K-Means and GMM agree with the designed personas.

## Pipeline position

```
sessionize → journey / HMM → features → segmentation (this file)
```

You need features first. HMM modes are optional extras in the full lab, not required by this toy.
