# Example guide — DFG (`03_dfg_example.py`)

## Goal (in plain English)

Build a **process map** of real **event→event** follows (not stages): what actually happens after a `page_view`, a `scroll`, etc., including **START** and **END**.

Toy twin of step02’s DFG helpers.

## How to run

```bash
python day-1/02_journey/examples/03_dfg_example.py
```

## Sample input & output

Source: `_shared/data/toy_sessions.csv`.

### INPUT (RAW)

Event-name path per session:

```text
  S1: page_view
  S2: page_view > scroll > engaged_read
  S3: page_view > scroll > engaged_read > subscription_view > subscribe_click
  S4: page_view > scroll > engaged_read > subscription_view > checkout_start > payment_success > subscription_active
```

### OUTPUT (PROCESSED)

Aggregated DFG edges (count + probability leaving `from_activity`):

```text
      from_activity         to_activity  count  probability
              START           page_view      4        1.000
          page_view              scroll      3        0.750
             scroll        engaged_read      3        1.000
       engaged_read   subscription_view      2        0.667
     checkout_start     payment_success      1        1.000
       engaged_read                 END      1        0.333
          page_view                 END      1        0.250
    payment_success subscription_active      1        1.000
    subscribe_click                 END      1        1.000
subscription_active                 END      1        1.000
  subscription_view     subscribe_click      1        0.500
  subscription_view      checkout_start      1        0.500
```

**Read it:** every visit START→page_view (4); S1 bounces page_view→END.

---

## Big picture (intuition)

Funnel/Markov use **stages**. DFG uses **exact event names** — the street map of clicks.

```text
load_toy_events()
      → directly_follows()   START / A→B / END edges
      → edge_table()         counts + P(to | from)
```

---

## High-level variables

| Name | Meaning |
|------|---------|
| `events` | Toy clickstream |
| `session` / `activity` | Arrays for pairwise follows |
| `same` / `is_first` / `is_last` | Edge construction flags |
| `edges` | Every observed follow (including START/END) |
| `table` | Aggregated edge counts + probability |
| `probability` | Share of follows leaving `from_activity` |

---

## Deep code walkthrough (every function)

### `directly_follows(events)`

**Job:** Emit three kinds of edges: `START→first`, consecutive events in-session, `last→END`.

### `edge_table(edges)`

**Job:** Group by from/to; count; row-normalize to probability; sort by count.

### `journey_variants(events)`

**Job:** Collapse consecutive repeat events and list each session path ending in `END` (helper for reading paths; main focuses on the edge table).

### `_section(title)` / `main()`

Print RAW paths; build edges; print PROCESSED edge table.

Uses: `describe_sessions()`, `load_toy_events()`.

---

## Teaching takeaway

Answer: *“Which click paths actually fire, and how often?”*
