# `_shared/` — toy inputs used by the examples

Tiny, hand-built datasets so every example can be checked on a whiteboard.

**Data files** live in [`data/`](data/) as CSVs. Regenerate with:

```bash
python day-1/_shared/generate_toy_data.py
```

| File | Used by | What it provides |
|------|---------|------------------|
| `data/toy_raw_events.csv` | `01_sessionize` | Raw clicks **without** `session_id` |
| `data/toy_sessions.csv` | Journey, HMM, Features | Already-sessionized mini journeys |
| `data/toy_audience.csv` | Segmentation | 12 cookies in 3 planted groups |

Examples never read `day-1/data/web_events.csv`.

| Loader | Reads |
|--------|--------|
| `toy_raw_events.py` → `load_raw_events()` | `data/toy_raw_events.csv` |
| `toy_sessions.py` → `load_toy_events()` | `data/toy_sessions.csv` |
| segmentation `toy_audience()` | `data/toy_audience.csv` |

---

## Why three toys?

| Need | Toy |
|------|-----|
| Prove 30-min cut + dedupe | `toy_raw_events.csv` |
| Prove Funnel/Markov/DFG/HMM/features math | `toy_sessions.csv` |
| Prove clustering recovers groups | `toy_audience.csv` |
