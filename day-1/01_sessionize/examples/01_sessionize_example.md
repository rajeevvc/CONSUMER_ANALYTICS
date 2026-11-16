# Example guide — Sessionize (`01_sessionize_example.py`)

## Goal (in plain English)

Turn a handful of raw clicks into **visits (sessions)** using the **30-minute idle** rule, then attach a **7-day conversion** label.

Toy-sized twin of `step01_sessionize.py` — small enough to check by hand.

## How to run

```bash
python day-1/01_sessionize/examples/01_sessionize_example.py
```

## Sample input & output

Source: `_shared/data/toy_raw_events.csv`. Designed quirks: A0001 has a 1s duplicate (drop) and a 35‑min gap (new session); A0004 converts.

### INPUT (RAW)

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Cookie / visitor id (same person across clicks) |
| `timestamp` | When the event happened |
| `event_name` | Action type (`page_view`, `scroll`, `checkout_start`, …) |
| `content_id` | Article / content key (used in near-duplicate check) |
| `device_type` | Device at capture (`desktop`, `mobile`, `tablet`) |
| `referrer` | How they arrived (often blank after the first hit) |

No `session_id` yet — this example creates it.

```text
anonymous_id           timestamp          event_name content_id device_type       referrer
       A0001 2026-01-10 10:00:00           page_view       C001     desktop organic_search
       A0001 2026-01-10 10:00:01           page_view       C001     desktop organic_search
       A0001 2026-01-10 10:05:00              scroll       C001     desktop            NaN
       A0001 2026-01-10 10:40:00           page_view       C002     desktop         direct
       A0002 2026-01-10 11:00:00           page_view       C010      mobile social_organic
       A0002 2026-01-10 11:00:30              scroll       C010      mobile            NaN
       A0002 2026-01-10 11:01:00        engaged_read       C010      mobile            NaN
       A0003 2026-01-10 12:00:00           page_view       C020      tablet          email
       A0003 2026-01-10 12:00:20              scroll       C020      tablet            NaN
       A0003 2026-01-10 12:01:00        engaged_read       C020      tablet            NaN
       A0003 2026-01-10 12:02:00   subscription_view       C020      tablet            NaN
       A0003 2026-01-10 12:02:30     subscribe_click       C020      tablet            NaN
       A0004 2026-01-10 13:00:00           page_view       C030     desktop organic_search
       A0004 2026-01-10 13:00:15              scroll       C030     desktop            NaN
       A0004 2026-01-10 13:01:00        engaged_read       C030     desktop            NaN
       A0004 2026-01-10 13:02:00   subscription_view       C030     desktop            NaN
       A0004 2026-01-10 13:03:00      checkout_start       C030     desktop            NaN
       A0004 2026-01-10 13:04:00     payment_success       C030     desktop            NaN
       A0004 2026-01-10 13:05:00 subscription_active        NaN     desktop            NaN
```

### OUTPUT (PROCESSED)

```text
session_id anonymous_id       session_start  duration_sec  n_behavior_events furthest_stage  converted
S000000001        A0001 2026-01-10 10:00:00         300.0                  2         scroll      False
S000000002        A0001 2026-01-10 10:40:00           0.0                  1        landing      False
S000000003        A0002 2026-01-10 11:00:00          60.0                  3        engaged      False
S000000004        A0003 2026-01-10 12:00:00         150.0                  5         intent      False
S000000005        A0004 2026-01-10 13:00:00         240.0                  6           deep       True
```

**Read it:** 19 raw → 18 after 2s dedupe → **5 sessions**. A0001 splits into 2 visits; only S000000005 converted.

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
