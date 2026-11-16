# Example guide — Feature engineering (`01_feature_engineering_example.py`)

## Goal (in plain English)

Turn toy events into **one numeric habit vector per cookie** — visits → session scorecards → user features ready for segmentation.

Toy twin of step01 summary + `step04_feature_engineering.user_features`.

## How to run

```bash
python day-1/04_feature_engineering/examples/01_feature_engineering_example.py
```

## Sample input & output

Source: `_shared/data/toy_sessions.csv`.

### INPUT (RAW)

| Column | Meaning |
|--------|---------|
| `session_idx` | Visit id |
| `anonymous_id` | Cookie — features will roll up to this key |
| `timestamp` | Event time (drives duration / recency) |
| `event_name` | Raw action (counted into rates; conversion flags outcomes) |
| `stage` | Funnel tag (drives depth / furthest stage) |

```text
 session_idx anonymous_id           timestamp          event_name        stage
           1        A0001 2026-01-10 10:00:00           page_view      landing
           2        A0002 2026-01-10 11:00:00           page_view      landing
           2        A0002 2026-01-10 11:00:30              scroll       scroll
           2        A0002 2026-01-10 11:01:00        engaged_read      engaged
           3        A0003 2026-01-10 12:00:00           page_view      landing
           3        A0003 2026-01-10 12:00:20              scroll       scroll
           3        A0003 2026-01-10 12:01:00        engaged_read      engaged
           3        A0003 2026-01-10 12:02:00   subscription_view       intent
           3        A0003 2026-01-10 12:02:30     subscribe_click       intent
           4        A0004 2026-01-10 13:00:00           page_view      landing
           4        A0004 2026-01-10 13:00:15              scroll       scroll
           4        A0004 2026-01-10 13:01:00        engaged_read      engaged
           4        A0004 2026-01-10 13:02:00   subscription_view       intent
           4        A0004 2026-01-10 13:03:00      checkout_start         deep
           4        A0004 2026-01-10 13:04:00     payment_success         deep
           4        A0004 2026-01-10 13:05:00 subscription_active subscription
```

### OUTPUT (PROCESSED)

One row per **cookie** (habit vector):

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Cookie key |
| `n_sessions` | How many visits this cookie had |
| `mean_duration_sec` | Average visit length (seconds) |
| `mean_furthest_rank` | Average depth (1=landing … 5=deep) |
| `share_intent` | Share of visits whose furthest stage was intent |
| `share_deep` | Share of visits that reached deep |
| `subscription_view_rate` | Share of behavior events that are plan views |
| `conversion_rate` | Share of visits that include a conversion |
| `recency_days` | Days since this cookie’s last visit (vs latest in the toy) |

```text
anonymous_id  n_sessions  mean_duration_sec  mean_furthest_rank  share_intent  share_deep  subscription_view_rate  conversion_rate  recency_days
       A0001           1                0.0                 1.0           0.0         0.0                   0.000              0.0         0.125
       A0002           1               60.0                 3.0           0.0         0.0                   0.000              0.0         0.083
       A0003           1              150.0                 4.0           1.0         0.0                   0.200              0.0         0.042
       A0004           1              240.0                 5.0           0.0         1.0                   0.167              1.0         0.000
```

**Read it:** A0001 depth=1 / convert=0; A0004 depth=5 / convert=1.0 (ready for segmentation).

---

## Big picture (intuition)

```text
load_toy_events()
      → session_features()   one row per visit
      → user_features()      one row per anonymous_id
      → print RAW / PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `STAGE_BY_EVENT` / `STAGE_RANK` | Event → stage → depth |
| `BEHAVIOR` | Event names counted into rates |
| `CONVERSION` | Outcome events that flag `converted` |
| `sessions` | Visit-level table |
| `users` / `features` | Cookie-level vectors |
| `share_intent` / `share_deep` | Mix of visit depths |
| `*_rate` | Event share of behavior volume |
| `recency_days` / `days_active` | Freshness and span |

---

## Deep code walkthrough (every function)

### `session_features(events)`

**Job:** For each session, compute duration, behavior count, furthest stage/rank, conversion flag, and per-event counts.

### `user_features(sessions)`

**Job:** Roll sessions to cookies:

1. Means: sessions, duration, depth, conversion.  
2. Stage mix → `share_intent`, `share_deep`, `share_landing_or_scroll`.  
3. Event totals / behavior sum → `*_rate`.  
4. `days_active`, `recency_days` vs latest snapshot.

### `_section(title)` / `main()`

Print RAW; build sessions + users; print PROCESSED preview columns.

Uses: `describe_sessions()`, `load_toy_events()`, `STAGE_BY_EVENT`.

---

## Teaching takeaway

Answer: *“What does this cookie’s habit look like?”*
