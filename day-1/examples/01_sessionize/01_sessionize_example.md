# `01_sessionize_example.py` — deep code walkthrough

**Question:** How do raw clicks become visits (sessions) plus a conversion label?

**Maps to lab:** `day-1/step01_sessionize.py`

**Run:**

```bash
conda activate awsproject
python day-1/examples/01_sessionize/01_sessionize_example.py
```

---

## Why this exists

Analytics rarely works on raw click rows. First you must decide:

1. Which rows are noise (near-duplicates)?
2. Which clicks belong to the same *visit*?
3. How deep did that visit go?
4. Did the cookie convert soon after?

This example is a **toy-sized copy** of the Day 1 sessionize step so you can verify every rule by hand.

---

## Input

Loaded from `examples/_shared/toy_raw_events.py` → `load_raw_events()`.

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Long-lived cookie / visitor ID |
| `timestamp` | Event time |
| `event_name` | Raw action (`page_view`, `scroll`, …) |
| `content_id` | Article / content key (used in dedupe) |
| `device_type` | Device at capture |
| `referrer` | Acquisition source (often null after first hit) |

**There is no `session_id` yet.** That is what this script creates.

Designed quirks in the toy:

- **A0001** has a near-duplicate `page_view` 1 second later (should drop).
- **A0001** then idles **35 minutes** before another `page_view` (should start a **new** session).
- **A0004** ends with `subscription_active` (conversion outcome).

---

## Constants (top of file)

| Constant | Value | Role |
|----------|-------|------|
| `SESSION_GAP_SECONDS` | `1800` (30 min) | Idle gap that ends a visit |
| `DUPLICATE_GAP_SECONDS` | `2` | Same cookie/event/content within 2s → drop |
| `HORIZON_DAYS` | `7` | Conversion window after session start |
| `CONVERSION_EVENTS` | `register_complete`, `subscription_active` | Outcomes, not browsing depth |
| `STAGE_BY_EVENT` | event → stage map | Funnel tags for each click |
| `STAGE_RANK` | landing=1 … deep=5 | Numeric depth for “furthest stage” |

**Important:** conversion stages (`registration`, `subscription`) are tagged on events, but **furthest browsing depth** only uses ranks 1–5. Conversion is labeled separately via `converted`.

---

## Imports / path bootstrap

```python
_EXAMPLES = Path(__file__).resolve().parents[1]
_SHARED = _EXAMPLES / "_shared"
sys.path.insert(0, str(_SHARED))
from toy_raw_events import describe_raw, load_raw_events
```

`parents[1]` is `examples/`. The script temporarily adds `_shared/` to `sys.path` so it can import the toy loader without installing a package.

---

## Function-by-function

### 1. `drop_near_duplicates(events)`

**Purpose:** Remove accidental double-fires (double-click, tracker retry).

**Logic:**

1. Sort by `anonymous_id`, `timestamp` (`mergesort` = stable).
2. Compute `gap` = seconds since *this cookie’s* previous event.
3. Mark a row as near-duplicate when **all** are true vs the previous row:
   - same cookie
   - same `event_name`
   - same `content_id` (null treated as `""`)
   - `gap ≤ 2` seconds
4. Keep rows that are **not** near-duplicates.

**Toy effect:** A0001’s second `page_view` at `10:00:01` on `C001` is dropped → 19 raw → 18 kept.

---

### 2. `sessionize(events)`

**Purpose:** Assign every kept event to a visit.

**Logic:**

1. Sort cookie + time again.
2. `gap = timestamp.diff()` **within cookie**.
3. `new_session = gap is NaN OR gap > 1800`.
   - First event for a cookie always starts a session (`NaN` gap).
4. `session_idx = cumsum(new_session)` → 1, 2, 3, …
5. Pretty id: `session_id = "S" + zero-padded index` (e.g. `S000000001`).
6. Map `event_name` → `stage`.
7. Flag `is_conversion` for outcome events.

**Toy effect:** A0001’s `10:40` event has gap `2100s > 1800` → second session for that cookie. Total sessions in the toy ≈ **5**.

---

### 3. `session_summary(events)`

**Purpose:** Collapse the event table to **one row per visit**.

**Logic:**

1. Split **behavior** = rows where `is_conversion` is False.
2. Aggregate all events for device/referrer/start/end/`n_events`.
3. On behavior only:
   - `n_behavior_events`
   - `furthest_rank` = max stage rank
   - `duration_sec` = last behavior time − first behavior time
4. Map `furthest_rank` back to `furthest_stage` name.

**Why exclude conversions from duration/depth?** Outcomes can fire after the browse path; depth should reflect engagement, not the billable event itself.

---

### 4. `attach_conversion_label(sessions, events)`

**Purpose:** Label each session with whether the cookie’s **first** conversion happens within 7 days of `session_start`.

**Logic (vectorized per cookie):**

1. Collect conversion timestamps per cookie, sorted.
2. For each session start, `searchsorted` finds the index of the next conversion time.
3. `already_converted` = there was already a conversion **before** this start (`next_index > 0`).
4. `converted` = this session is still before the first conversion **and** `(first_conversion_time - start) ≤ 7 days`.

**Toy effect:** A0004’s visit contains `subscription_active` → that session gets `converted=True`.

---

---

## `main()` pipeline (what runs)

```
raw events
  → drop_near_duplicates
  → sessionize          (event table + session_id + stage)
  → session_summary     (one row per visit)
  → attach_conversion_label
  → print RAW + PROCESSED only
```

| Printed block | What you see |
|---------------|--------------|
| **RAW** | Input clickstream |
| **PROCESSED** | One session scorecard row per visit |

---

## Sample terminal output (what you see when you run it)

The script prints **two** blocks only: **RAW** then **PROCESSED**.

### RAW — input events

```text
anonymous_id           timestamp          event_name content_id device_type       referrer
       A0001 2026-01-10 10:00:00           page_view       C001     desktop organic_search
       A0001 2026-01-10 10:00:01           page_view       C001     desktop organic_search
       A0001 2026-01-10 10:05:00              scroll       C001     desktop            NaN
       A0001 2026-01-10 10:40:00           page_view       C002     desktop         direct
       … (A0002–A0004) …
       A0004 2026-01-10 13:05:00 subscription_active        NaN     desktop            NaN
```

**How to read it:** Unsessionized clicks. A0001 has a 1-second duplicate and a 35-minute idle before the next page_view.

### PROCESSED — session summary

```text
session_id anonymous_id       session_start  duration_sec  n_behavior_events furthest_stage  converted
S000000001        A0001 2026-01-10 10:00:00         300.0                  2         scroll      False
S000000002        A0001 2026-01-10 10:40:00           0.0                  1        landing      False
S000000003        A0002 2026-01-10 11:00:00          60.0                  3        engaged      False
S000000004        A0003 2026-01-10 12:00:00         150.0                  5         intent      False
S000000005        A0004 2026-01-10 13:00:00         240.0                  6           deep       True

Note: 19 raw events → 18 after 2s dedupe → 5 sessions (30-min gap).
A0001 splits into 2 visits; only S000000005 converted.
```

**How to read it:** One row per visit. A0001 appears twice (30-min cut). Only A0004’s visit is `converted=True`.

## Hand checks you should get

| Check | Expect |
|-------|--------|
| A0001 session count | `2` |
| A0001 gap at 10:40 | `2100` seconds |
| Events after dedupe | `18` (raw `19`) |
| Total sessions | `5` |
| Converted session | `S000000005` (A0004) |

---

## Concepts to remember

- **Cookie** (`anonymous_id`) = identity across days.
- **Session** (`session_id`) = one visit, cut at 30 minutes idle.
- **Stage** = rule-based funnel tag on an event.
- **Converted** = outcome label on a *session*, with a time horizon.

## What comes next

Sessionized events / summaries feed:

- Journey (Funnel / Markov / DFG) — stages & paths  
- HMM — latent modes inside visits  
- Feature engineering — session → user vectors  
- Segmentation — audience clusters  
