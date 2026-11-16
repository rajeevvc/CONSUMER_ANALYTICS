# Day 1 data

Full lab tables for sessionization and inventory checks live in this folder.

| File | Role | How stored |
|------|------|------------|
| `web_events.csv` | Main clickstream (sessionize) | Git LFS (~156MB) |
| `web_events.parquet` | Same for DuckDB path | Git LFS |
| `app_events.csv` / `.parquet` | Inventory / app events | Git LFS |
| `content_catalog.csv` / `.parquet` | Content metadata | Git (CSV) / LFS (parquet) |
| `subscriptions.csv` / `.parquet` | Subscription records | Git (CSV) / LFS (parquet) |

After clone, pull LFS objects:

```bash
git lfs install
git lfs pull
```

Then run:

```bash
python day-1/01_sessionize/step01_sessionize.py
```

Required for sessionize inventory: `web_events.csv`, `app_events.csv`, `content_catalog.csv`, `subscriptions.csv`.
