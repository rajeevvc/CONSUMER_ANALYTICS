# Learner guide — Behavioral segmentation (`step05_behavioral_segmentation.py`)

## Goal

Cluster **cookies** into audience segments using user-level features.

Algorithms in this lab:
- **K-Means** (hard clusters)  
- **GMM** / Gaussian Mixture (soft components; label = argmax)

Compare both on the same scaled feature matrix and profile the segments.

## How to run

```bash
conda activate awsproject
python day-1/04_feature_engineering/step04_feature_engineering.py      # prerequisite
python day-1/05_segmentation/step05_behavioral_segmentation.py
```

### Tiny worked example

```bash
python day-1/05_segmentation/examples/01_segmentation_example.py
```

See the paired `examples/` folder in this context directory.

## Input

| File | Role |
|------|------|
| `day-1/output/user_features.csv` | **Required** (rebuild from sessions if missing) |

### Feature columns used for clustering

`n_sessions`, `mean_duration_sec`, `mean_behavior_events`, `mean_content`,  
`mean_furthest_rank`, `share_deep`, `share_intent`, `share_engaged`,  
`share_landing_or_scroll`,  
`page_view_rate`, `scroll_rate`, `engaged_read_rate`, `share_rate`,  
`login_rate`, `register_start_rate`, `subscription_view_rate`,  
`subscribe_click_rate`, `checkout_start_rate`, `payment_success_rate`,  
`conversion_rate`

Also need `anonymous_id` as the key (not used as a numeric feature).

## What you must implement

1. **Load & clean** — coerce numerics; fill NaNs; optionally cap extreme durations  
2. **Scale** — `StandardScaler`  
3. **Choose k** — try k = 3…8; pick best silhouette on a sample  
4. **Fit K-Means** with that k  
5. **Fit GMM** with the same number of components (report BIC/AIC + silhouette)  
6. **Name segments** heuristically from profile means (converters, intent_engaged, bouncers, …)  
7. **Write** audience assignments + profile tables + metrics JSON  

### Suggested naming heuristics (example)

| Condition | Label idea |
|-----------|------------|
| High conversion rate | `converters` |
| High furthest rank (deep) | `deep_checkout` |
| High intent + plan views | `intent_engaged` |
| Mid depth | `regular_readers` |
| Low depth | `bouncers` / `casual_browsers` |

## Output

| File | Content |
|------|---------|
| `day-1/output/audience_segments.csv` | Cookie + K-Means/GMM segment ids & labels |
| `day-1/output/segment_profiles_kmeans.csv` | Segment scorecards |
| `day-1/output/segment_profiles_gmm.csv` | Segment scorecards |
| `day-1/output/segmentation_metrics.json` | k, silhouette, BIC/AIC, feature list |

## Acceptance checks

- One row per cookie in `audience_segments.csv`  
- Profile rows sum of `readers` ≈ total cookies  
- Metrics JSON includes both `kmeans` and `gmm`  

## Teaching takeaway

Answer: *“What kind of audience is this visitor over time?”* (user clustering — not within-session modes).

## Contrast with HMM

| | HMM state modeling | This segmentation |
|--|--------------------|-------------------|
| Grain | Event / latent mode | Cookie / segment |
| Input | Sessionized events | User features |
| Question | How are they reading now? | Who are they as an audience? |
