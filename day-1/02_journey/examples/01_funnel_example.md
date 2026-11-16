# Example guide — Funnel (`01_funnel_example.py`)

## Goal (in plain English)

From staged events, build a **ladder**: how many sessions reached each stage, and what share also reached the **next** stage (`advance_rate`).

Toy twin of `step02_journey_analysis.funnel_table`.

## How to run

```bash
python day-1/02_journey/examples/01_funnel_example.py
```

## Sample input & output

Source: `_shared/data/toy_sessions.csv`.

### INPUT (RAW)

| Column | Meaning |
|--------|---------|
| `session_idx` | Visit id (`1`…`4` in the toy) |
| `anonymous_id` | Cookie / visitor for that visit |
| `timestamp` | When the event happened |
| `event_name` | Raw action (`page_view`, `scroll`, …) |
| `stage` | Funnel tag mapped from `event_name` (`landing`…`subscription`) |

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

```text
       stage  events  sessions_containing_stage  sessions_ending_here   next_stage  advance_rate
     landing       4                          4                     1       scroll        0.7500
      scroll       3                          3                     0      engaged        1.0000
     engaged       3                          3                     1       intent        0.6667
      intent       3                          2                     1         deep        0.5000
        deep       2                          1                     0 registration        0.0000
registration       0                          0                     0 subscription           NaN
subscription       1                          1                     1          NaN           NaN
```

**Read it:** `advance_rate` = share that also hit the **next** stage (ever), not next click. landing→scroll = 0.75; intent→deep = 0.50 (cliff).

---

## Big picture (intuition)

A funnel is not “next click.” It asks: *did this visit ever touch stage X, and also ever touch stage X+1?*

```text
load_toy_events() → funnel_table() → print RAW / PROCESSED
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `FUNNEL_STAGES` | Ordered ladder from `_shared/toy_sessions` |
| `events` | Toy sessionized events with stages |
| `presence` / `contains` | Which stages appear in each session |
| `furthest` | Deepest stage index per session |
| `table` | Final funnel DataFrame |
| `advance_rate` | Containing-next / containing-this |

---

## Deep code walkthrough (every function)

### `funnel_table(events)`

**Job:** Build the scorecard.

1. Count events per stage.  
2. Mark stages present in each session.  
3. Find furthest stage per session.  
4. For each stage: sessions containing it, ending here, advance rate to next.

### `_section(title)` / `main()`

Print banners; load toys; show RAW events; print PROCESSED funnel.

Uses: `describe_sessions()`, `load_toy_events()`, `FUNNEL_STAGES`.

---

## Teaching takeaway

Answer: *“Where does the ladder thin out?”* (toy note: landing→scroll strong; intent→deep is the cliff.)
