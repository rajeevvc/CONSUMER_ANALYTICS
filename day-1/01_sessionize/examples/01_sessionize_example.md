# Example guide — Sessionize (`01_sessionize_example.py`)

## Goal (in plain English)

Turn a handful of raw clicks into **visits (sessions)** using the **30-minute idle** rule, then attach a **7-day conversion** label.

Toy-sized twin of `step01_sessionize.py` — small enough to check by hand.

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/examples/01_sessionize_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Click rows from `_shared/data/toy_raw_events.csv` |
| **PROCESSED** | One scorecard row per visit |

Designed quirks: A0001 has a 1s duplicate (drop) and a 35‑min gap (new session); A0004 converts.

---

## Big picture (intuition)

```text
load_raw_events()
      │
      ▼
 drop_near_duplicates()   ← remove double-clicks ≤2s
      │
      ▼
 sessionize()             ← cut when idle > 30 min
      │
      ├── session_summary()
      └── attach_conversion_label()
             │
             ▼
        print RAW then PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `_DAY1` / `_SHARED` | Paths so the example can import toy loaders |
| `SESSION_GAP_SECONDS` | 1800 — new visit threshold |
| `DUPLICATE_GAP_SECONDS` | 2 — near-duplicate window |
| `HORIZON_DAYS` | 7 — conversion look-ahead |
| `CONVERSION_EVENTS` | `register_complete`, `subscription_active` |
| `STAGE_BY_EVENT` / `STAGE_RANK` | Event → stage → depth number |
| `raw` | Original toy events |
| `cleaned` | After dedupe |
| `events` | Sessionized events |
| `sessions` | One row per visit with `converted` |

---

## Deep code walkthrough (every function)

### `drop_near_duplicates(events)`

**Job:** Drop same cookie + same event + same content within 2 seconds.

### `sessionize(events)`

**Job:** Sort by cookie/time; compute gap; start a new session when first event or gap > 30 min; add `session_id`, `stage`, `is_conversion`.

### `session_summary(events)`

**Job:** One row per visit — start/end, device, referrer, behavior counts, furthest stage, duration.

### `attach_conversion_label(sessions, events)`

**Job:** For each cookie, if the first conversion is within 7 days of a session start → `converted`; if conversion already happened earlier → `already_converted`.

### `_section(title)`

**Job:** Print a clear RAW / PROCESSED banner.

### `main()`

```text
describe_raw → print RAW → dedupe → sessionize → summarize → label → print PROCESSED
```

Also uses shared helpers: `load_raw_events()`, `describe_raw()`.

---

## Teaching takeaway

Answer: *“Which clicks are one visit, and did membership happen soon after?”*
