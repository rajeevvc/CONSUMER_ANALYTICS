# Example guide — Segmentation (`01_segmentation_example.py`)

## Goal (in plain English)

Cluster **12 toy cookies** into named audiences with **K-Means** and **GMM**.

Toy twin of `step05_behavioral_segmentation.py` — three planted groups (bouncers / readers / converters) so you can see recovery by eye.

## How to run

```bash
conda activate awsproject
python day-1/05_segmentation/examples/01_segmentation_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Hand-built user features + truth `persona` |
| **PROCESSED** | `kmeans_label` and `gmm_label` per cookie |

---

## Big picture (intuition)

```text
toy_audience()          loads _shared/data/toy_audience.csv
      │
      ▼
 fit_segmentation()     scale → choose k → K-Means + GMM → name
      │
      ▼
 print RAW / PROCESSED  (profile() helper available for scorecards)
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `FEATURE_COLUMNS` | Numeric axes used for clustering |
| `persona` | Planted truth label (not fed to the model) |
| `matrix` / `scaled` | Raw vs standardized feature matrix |
| `best_k` | k with best silhouette (designed to be 3) |
| `kmeans_segment` / `gmm_segment` | Integer cluster ids |
| `kmeans_label` / `gmm_label` | Friendly names |
| `scores` | List of `(k, silhouette)` trials |

---

## Deep code walkthrough (every function)

### `toy_audience()`

**Job:** Build 12 cookies in 3 obvious groups with different depth/conversion patterns.

### `name_segment(part)`

**Job:** Heuristic name from group averages — converters if conversion high, else regular_readers if depth mid/high, else bouncers.

### `fit_segmentation(users)`

**Job:**

1. Scale `FEATURE_COLUMNS`.  
2. Try k = 2…4; pick max silhouette.  
3. Fit K-Means and GMM at that k.  
4. Map ids → names (`unique_map` avoids duplicate labels).  
5. Store `k`, silhouette trials, GMM BIC on `out.attrs`.

**Returns:** Labeled audience DataFrame.

### `profile(frame, segment_col, label_col)`

**Job:** Small scorecard per segment (size, depth, conversion, deep share). Available for inspection; main prints assignments.

### `_section(title)` / `main()`

Print RAW features; fit; print PROCESSED labels vs planted personas.

---

## Teaching takeaway

Answer: *“Which audience is this cookie?”* — K-Means (hard) and GMM (soft→argmax) should both recover the three planted groups on this toy.
