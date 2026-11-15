# Learner guide — Sessionization (`step01_sessionize.py`)

## Goal

Turn raw web clickstream into **visits (sessions)** using a **30-minute inactivity** rule, then summarize each visit and attach a **7-day conversion** label.

## How to run

```bash
conda activate awsproject
python day-1/step01_sessionize.py
```

## Input

| File | Used? |
|------|--------|
| `day-1/data/web_events.csv` | **Yes** — only table processed |
| `day-1/data/app_events.csv` | Inventory only (must exist) |
| `day-1/data/content_catalog.csv` | Inventory only |
| `day-1/data/subscriptions.csv` | Inventory only |

**Columns read from web events:**  
`anonymous_id`, `timestamp`, `event_name`, `content_id`, `device_type`, `referrer`

Ignore any generator `session_id` — rebuild sessions yourself.

## What you must implement

1. **Inventory** — confirm the four data files exist; print row counts  
2. **Load & clean** — parse timestamps; drop bad rows; sort by cookie + time  
3. **Near-duplicate drop** — same cookie + event + content within **2 seconds** → drop  
4. **Tag events**
   - Map `event_name` → `stage` (see ladder below)  
   - `is_conversion` for `register_complete`, `subscription_active`  
5. **Sessionize** — per cookie, new session if gap since previous event **> 1800s**  
6. **Session summary** — one row per session (duration, furthest stage, event counts)  
7. **Conversion label** — `converted` if first conversion is within **7 days** of session start; `already_converted` if conversion happened earlier  

### Stage ladder (furthest depth)

| Rank | Stage | Events |
|------|--------|--------|
| 1 | landing | `page_view`, `login` |
| 2 | scroll | `scroll` |
| 3 | engaged | `engaged_read` |
| 4 | intent | `share`, `subscription_view`, `subscribe_click` |
| 5 | deep | `checkout_start`, `payment_success` |

Also map register/activate events to `registration` / `subscription` (outcomes; not part of furthest 1–5).

## Output

| File | Grain |
|------|--------|
| `day-1/output/sessionized_events.csv` | Event + `session_id`, `stage`, `gap_seconds`, `is_conversion` |
| `day-1/output/sessions.csv` | Session summary + `converted`, `already_converted` |

## Acceptance checks

- Same cookie with a 40‑minute gap → **two** sessions  
- Same cookie with a 10‑minute gap → **one** session  
- Furthest stage uses max rank among **non-conversion** behavior events  
- Downstream scripts can read both CSVs  

## Cookie vs session

- **Cookie** = long-lived visitor ID  
- **Session** = one visit; ends after 30 min idle — **not** when the cookie expires  
