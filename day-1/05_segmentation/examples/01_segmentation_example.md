# Example guide — Segmentation (`01_segmentation_example.py`)

## Goal (in plain English)

Cluster **12 toy cookies** into named audiences with **K-Means** and **GMM**.

Toy twin of `step05_behavioral_segmentation.py` — three planted groups (bouncers / readers / converters) so you can see recovery by eye.

## How to run

```bash
python day-1/05_segmentation/examples/01_segmentation_example.py
```

## Sample input & output

Source: `_shared/data/toy_audience.csv`.

### INPUT (RAW)

```text
anonymous_id         persona  mean_furthest_rank  conversion_rate  share_deep
          B1   bouncer_truth                 1.0              0.0         0.0
          B2   bouncer_truth                 1.0              0.0         0.0
          B3   bouncer_truth                 1.0              0.0         0.0
          B4   bouncer_truth                 1.0              0.0         0.0
          R1    reader_truth                 3.0              0.0         0.0
          R2    reader_truth                 3.2              0.0         0.0
          R3    reader_truth                 3.4              0.0         0.0
          R4    reader_truth                 3.6              0.0         0.0
          C1 converter_truth                 4.5              0.4         0.3
          C2 converter_truth                 4.6              0.5         0.3
          C3 converter_truth                 4.7              0.6         0.3
          C4 converter_truth                 4.8              0.7         0.3
```

### OUTPUT (PROCESSED)

```text
anonymous_id         persona    kmeans_label       gmm_label
          B1   bouncer_truth        bouncers        bouncers
          B2   bouncer_truth        bouncers        bouncers
          B3   bouncer_truth        bouncers        bouncers
          B4   bouncer_truth        bouncers        bouncers
          R1    reader_truth regular_readers regular_readers
          R2    reader_truth regular_readers regular_readers
          R3    reader_truth regular_readers regular_readers
          R4    reader_truth regular_readers regular_readers
          C1 converter_truth      converters      converters
          C2 converter_truth      converters      converters
          C3 converter_truth      converters      converters
          C4 converter_truth      converters      converters
```

**Read it:** chosen k=3; both methods recover bouncers / regular_readers / converters. `persona` is truth-only (not used by the model).

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

**Job:** Load 12 cookies in 3 obvious groups from `toy_audience.csv`.

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
