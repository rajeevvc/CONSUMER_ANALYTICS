# Day 1 data

Small catalog tables may be in this folder. Large clickstream extracts are **not** in git (GitHub 100MB file limit):

- `web_events.csv` (~156MB)
- `app_events.csv` (~33MB, also omitted for size)
- `*.parquet`

Copy them from your lab data pack / generator into this folder before running:

```bash
python day-1/sessionize.py
```

Required for sessionize inventory: `web_events.csv`, `app_events.csv`, `content_catalog.csv`, `subscriptions.csv`.
