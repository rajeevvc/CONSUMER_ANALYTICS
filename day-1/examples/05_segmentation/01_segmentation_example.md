# `01_segmentation_example.py` — deep code walkthrough

**Question:** Which audience group does each cookie belong to?

**Maps to lab:** `day-1/step05_behavioral_segmentation.py`

**Run:**

```bash
conda activate awsproject
python day-1/examples/05_segmentation/01_segmentation_example.py
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

| Section | Content |
|---------|---------|
| OUTPUT 1 | Toy audience + persona counts |
| OUTPUT 2 | Silhouette by k + chosen k + GMM BIC |
| OUTPUT 3 | Assignments + agreement vs persona family |
| OUTPUT 4 | K-Means / GMM profiles |
| OUTPUT 5 | Acceptance checks |

### Agreement check

Personas are `bouncer_truth` / `reader_truth` / `converter_truth`. Labels are `bouncers` / `regular_readers` / `converters`. The script maps families and reports match rate — toy is designed for **~100%**.

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

## Pipeline position

```
sessionize → journey / HMM → features → segmentation (this file)
```

You need features first. HMM modes are optional extras in the full lab, not required by this toy.
