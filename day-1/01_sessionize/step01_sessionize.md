# Learner guide — Sessionization (`step01_sessionize.py`)

## Goal

Turn raw web clickstream into **visits (sessions)** using a **30-minute inactivity** rule, then summarize each visit and attach a **7-day conversion** label.

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py
```

### Tiny worked example

```bash
python day-1/01_sessionize/examples/01_sessionize_example.py
```

See the paired `examples/` folder in this context directory.

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

## Output

| File | Grain |
|------|--------|
| `day-1/output/sessionized_events.csv` | Event + `session_id`, `stage`, `gap_seconds`, `is_conversion` |
| `day-1/output/sessions.csv` | Session summary + `converted`, `already_converted` |

## Cookie vs session

- **Cookie** = long-lived visitor ID  
- **Session** = one visit; ends after 30 min idle — **not** when the cookie expires  

---

## Deep code walkthrough

### Paths and constants

```python
DAY1 = Path(__file__).resolve().parents[1]   # day-1/
DATA = DAY1 / "data"
OUTPUT = DAY1 / "output"
```

| Constant | Value | Meaning |
|----------|-------|---------|
| `SESSION_GAP_SECONDS` | `1800` | Idle gap that starts a new visit |
| `DUPLICATE_GAP_SECONDS` | `2` | Near-duplicate window |
| `HORIZON_DAYS` | `7` | Conversion attribution window |
| `CONVERSION_EVENTS` | register/subscribe activate | Outcomes, not browse depth |
| `STAGE_BY_EVENT` | event → stage map | Funnel tags |
| `STAGE_RANK` | landing=1 … deep=5 | Numeric depth for furthest stage |
| `BEHAVIOR_EVENTS` | list of browse events | Counted in session summary |

`STAGE_RANK` deliberately **excludes** registration/subscription — those are outcomes.

---

### 1. `collect_inventory()`

Confirms the four raw tables exist and returns row counts. Raises if any file is missing. This is the “event collection” checklist before processing.

### 2. `load_web_events()`

1. `_validate_web_header()` — required columns present  
2. `read_csv` with only `WEB_USECOLS` (ignores generator `session_id`)  
3. Parse timestamps; drop rows missing cookie/time/event  
4. Reject **unknown** `event_name` values (forces taxonomy sync)  
5. Sort cookie + time (`mergesort` = stable)  
6. `_drop_near_duplicates`  
7. Map `stage`, flag `is_conversion`  

**Why ignore raw `session_id`?** The generator’s sessions are not the lab’s 30-minute rule. Day 1 always rebuilds.

### 3. `_drop_near_duplicates(events)`

Marks a row as duplicate when **all** hold vs the previous row:

- same cookie  
- same `event_name`  
- same `content_id` (null → `""`)  
- gap ≤ 2 seconds  

Keeps everything else. Removes tracker double-fires without deleting real revisits.

### 4. `sessionize(events)`

```text
gap = seconds since this cookie's previous event
new_session = gap is NaN  OR  gap > 1800
session_idx = cumsum(new_session)
session_id  = "S" + zero-padded index
```

- First event for a cookie always starts a session (`NaN` gap).  
- `gap_seconds` is stored for auditing.

### 5. `session_summary(events)`

One row per `session_idx`:

| Field | How |
|-------|-----|
| start/end, device, referrer | from all events |
| `n_behavior_events`, duration | **non-conversion** events only |
| `furthest_rank` / `furthest_stage` | max `STAGE_RANK` on behavior |
| per-event counts | `page_view`, `scroll`, … from `BEHAVIOR_EVENTS` |

Duration = last behavior timestamp − first behavior timestamp (not conversion-only tails).

### 6. `attach_conversion_label(sessions, events)`

Per cookie:

1. Collect sorted conversion timestamps.  
2. For each session start, `searchsorted` finds the next conversion.  
3. `already_converted` = a conversion already happened **before** this start.  
4. `converted` = this session is still before the **first** conversion **and** `(first_conversion − start) ≤ 7 days`.

Only the first converting opportunity is labeled; later sessions after conversion get `already_converted=True`.

### 7. `main()` pipeline

```text
inventory → load_web_events → sessionize → session_summary
         → attach_conversion_label → write CSVs + print stats
```

Prints event mix and furthest-stage distribution so you can sanity-check the taxonomy.

---

## Acceptance checks

- Same cookie with a 40‑minute gap → **two** sessions  
- Same cookie with a 10‑minute gap → **one** session  
- Furthest stage uses max rank among **non-conversion** behavior events  
- Downstream scripts can read both CSVs  

## Teaching takeaway

Raw clicks → visits with depth + conversion labels. Everything later (Journey, HMM, Features) starts here.
