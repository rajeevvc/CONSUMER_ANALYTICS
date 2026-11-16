# Example guide — DFG (`03_dfg_example.py`)

## Goal (in plain English)

Build a **process map** of real **event→event** follows (not stages): what actually happens after a `page_view`, a `scroll`, etc., including **START** and **END**.

Toy twin of step02’s DFG helpers.

## How to run

```bash
conda activate awsproject
python day-1/02_journey/examples/03_dfg_example.py
```

## Input / Output (terminal)

| Section | What you see |
|---------|----------------|
| **RAW** | Event-name path per session |
| **PROCESSED** | Aggregated edges with counts + probabilities |

---

## Big picture (intuition)

Funnel/Markov use **stages**. DFG uses **exact event names** — the street map of clicks.

```text
load_toy_events()
      → directly_follows()   START / A→B / END edges
      → edge_table()         counts + P(to | from)
      → (journey_variants defined for teaching; main prints edges)
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

Answer: *“Which click paths actually fire, and how often?”* (toy: every visit START→page_view; S1 bounces page_view→END.)
