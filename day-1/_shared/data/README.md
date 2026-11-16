# Example toy data

Hand-built CSVs used by Day 1 **examples** (not the full lab under `day-1/data/`).

| File | Used by |
|------|---------|
| `toy_raw_events.csv` | Sessionize example |
| `toy_sessions.csv` | Funnel, Markov, DFG, HMM, Features examples |
| `toy_audience.csv` | Segmentation example |

Regenerate:

```bash
python day-1/_shared/generate_toy_data.py
```

Loaders: `toy_raw_events.py`, `toy_sessions.py`, and `toy_audience()` in the segmentation example.
