# Learner guide — Sessionization (`step01_sessionize.py`)

## Goal (in plain English)

Raw clickstream is a long list of tiny actions (page view, scroll, checkout…).

This step answers: **“Where does one visit end and the next begin?”**

Rule: if the same cookie is idle for **more than 30 minutes**, start a **new session**. Then summarize each visit and ask: **did this cookie register/subscribe within 7 days?**

## How to run

```bash
conda activate awsproject
python day-1/01_sessionize/step01_sessionize.py
```

### Tiny worked example

```bash
python day-1/01_sessionize/examples/01_sessionize_example.py
```

## Input / Output

| Input | Role |
|-------|------|
| `day-1/data/web_events.csv` | **Processed** — the clickstream |
| `app_events.csv`, `content_catalog.csv`, `subscriptions.csv` | **Inventory only** (must exist) |

| Output | Grain |
|--------|--------|
| `day-1/output/sessionized_events.csv` | One row per event + session id |
| `day-1/output/sessions.csv` | One row per visit |

Ignore any generator `session_id` in the raw file — this script rebuilds sessions.

---

## Big picture (intuition)

Think of a cookie’s timeline as a string of beads. Whenever the gap between beads is longer than 30 minutes, cut the string. Each piece is a **session (visit)**.

```text
web_events.csv
      │
      ▼
 collect_inventory()     ← are raw files present?
      │
      ▼
 load_web_events()       ← clean, dedupe, map stage
      │
      ▼
 sessionize()            ← cut at 30-min gaps
      │
      ├──► session_summary()           ← one row per visit
      │              │
      │              ▼
      └──► attach_conversion_label()   ← 7-day convert flag
                    │
                    ▼
           write CSVs + print stats
```

---

## High-level variables (what they mean)

### Path / config constants

| Name | What it is |
|------|------------|
| `DAY1` | Folder `day-1/` |
| `DATA` / `OUTPUT` | `day-1/data/` and `day-1/output/` |
| `WEB_EVENTS` … | Paths to raw tables |
| `WEB_USECOLS` | Columns actually loaded from web events |
| `SESSION_GAP_SECONDS` | `1800` (30 minutes) — gap that starts a new visit |
| `DUPLICATE_GAP_SECONDS` | `2` — near-duplicate window |
| `HORIZON_DAYS` | `7` — conversion look-ahead |
| `CONVERSION_EVENTS` | `register_complete`, `subscription_active` |
| `STAGE_BY_EVENT` | Maps each event name → funnel stage |
| `STAGE_RANK` | Numeric depth: landing=1 … deep=5 |
| `BEHAVIOR_EVENTS` | Event names counted on session summaries |
| `KNOWN_EVENTS` | Allowed event names (anything else → error) |

### Objects created while running

| Name | What it is |
|------|------------|
| `inventory` | Row counts for the four raw tables |
| `events` | Cleaned clickstream (later with `session_id`) |
| `gap` | Seconds since previous event for the same cookie |
| `new_session` | True when first event or gap > 30 min |
| `session_idx` | Running integer id of the visit |
| `sessions` / `summary` | One row per visit with counts and labels |
| `converted` | True if first conversion falls within 7 days of this visit |
| `already_converted` | True if cookie had converted *before* this visit |

### Important columns on outputs

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Cookie / visitor key |
| `session_id` | Visit id like `S000000001` |
| `stage` | Funnel stage of this event |
| `is_conversion` | Event is register/subscribe complete |
| `gap_seconds` | Idle time before this event |
| `furthest_stage` / `furthest_rank` | Deepest behavior stage in the visit |
| `duration_sec` | Length of the behavior part of the visit |
| `n_behavior_events` / `n_content` | Activity volume |
| per-event count columns | How many page_views, scrolls, … in the visit |

---

## Deep code walkthrough (every function)

### `collect_inventory()`

**Job:** Confirm the four raw tables exist and count rows.

Uses `_row_count()` (lines in file minus header). Missing file → `FileNotFoundError`.

**Returns:** `{ "web_events": N, "app_events": N, ... }`

---

### `_row_count(path)`

**Job:** Fast line count for inventory. Missing path → `None`.

---

### `_validate_web_header()`

**Job:** Read only the CSV header; check every `WEB_USECOLS` column exists before loading millions of rows.

---

### `load_web_events()`

**Job:** Load and tidy the clickstream used for Day 1.

**Steps:**

1. Validate header.  
2. Read only needed columns; parse timestamps.  
3. Drop rows missing cookie / time / event.  
4. Reject unknown `event_name` values.  
5. Sort by cookie, then time.  
6. Drop near-duplicates (`_drop_near_duplicates`).  
7. Map `stage` from `STAGE_BY_EVENT`; flag `is_conversion`.

**Returns:** Clean event DataFrame (not yet sessionized).

---

### `_drop_near_duplicates(events)`

**Job:** Remove “double-click” noise.

Keep a row unless it is the **same cookie + same event + same content** within **2 seconds** of the previous kept row.

**Returns:** Deduped events.

---

### `sessionize(events, gap_seconds=SESSION_GAP_SECONDS)`

**Job:** Cut the timeline into visits.

**Steps:**

1. Sort by cookie, time.  
2. Compute `gap` = seconds since previous event **for that cookie**.  
3. `new_session` = first event for cookie **or** gap > 30 minutes.  
4. `session_idx` = running sum of `new_session` (global integer).  
5. Build readable `session_id` = `S` + zero-padded index.

**Returns:** Events with `session_idx`, `session_id`, `gap_seconds`.

---

### `session_summary(events)`

**Job:** Collapse each visit into one scorecard.

**Steps:**

1. Split **behavior** events (exclude conversion events) for depth/duration.  
2. Aggregate per `session_idx`: start/end, device, referrer, event counts.  
3. Behavior stats: duration, unique content, furthest stage/rank.  
4. Pivot per-event counts (`page_view`, `scroll`, …).  
5. Fill missing behavior columns with 0.

**Returns:** One row per session.

---

### `attach_conversion_label(sessions, events, horizon_days=7)`

**Job:** Label each browsing visit with a future outcome.

**Intuition:** For each cookie, look at conversion timestamps. For a session that starts **before** any conversion:

- If the **first** conversion is within 7 days → `converted = True`.  
- If a conversion already happened earlier → `already_converted = True` (not a “still anonymous” success case).

Uses `searchsorted` so it stays fast on large data.

**Returns:** Sessions with `converted` and `already_converted`.

---

### `main()`

**Job:** Run the pipeline and print a human summary.

```text
mkdir output
inventory = collect_inventory()
events    = sessionize(load_web_events())
sessions  = attach_conversion_label(session_summary(events), events)
write CSVs
print event mix, furthest stage, 7-day convert rate among still-anonymous visits
```

---

## Acceptance checks

- Every event has a `session_id`  
- Gaps inside a session are ≤ 30 minutes (except the first event)  
- `sessions.csv` has one row per `session_id`  
- Conversion rate is only meaningful on visits that are not `already_converted`

## Teaching takeaway

Answer: *“What is one visit, and did it lead toward membership soon after?”*
