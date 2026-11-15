# `03_dfg_example.py` — deep code walkthrough

**Question:** What exact event→event paths actually happen? (process map)

**Maps to lab:** `day-1/step02_journey_analysis.py` → DFG / directly-follows helpers

**Run:**

```bash
conda activate awsproject
python day-1/examples/02_journey/03_dfg_example.py
```

---

## Why this exists

Funnel and Markov collapse clicks into **stages**. A **Directly-Follows Graph (DFG)** keeps **raw event names** so you can see process detail:

- Does every visit start with `page_view`?
- How often is `page_view → scroll` vs bounce `page_view → END`?
- What variants of full journeys exist?

This is process-mining style analysis on clickstreams.

---

## Input

Same `toy_sessions.load_toy_events()` — uses `event_name`, **not** `stage`, for the graph.

---

## Function 1: `directly_follows(events)`

Builds every observed edge instance.

### Sort and arrays

```python
train = events.sort_values(["session_idx", "timestamp"], kind="mergesort")
session = train["session_idx"].to_numpy()
activity = train["event_name"].to_numpy()
```

### Three edge families

1. **START → first event** of each session  
2. **event → next event** when still in the same session  
3. **last event → END** of each session  

```python
same = session[1:] == session[:-1]
is_first[1:] = session[1:] != session[:-1]
is_last[:-1] = session[1:] != session[:-1]
```

Returned columns:

| Column | Meaning |
|--------|---------|
| `from_activity` | Source node (`START` or event name) |
| `to_activity` | Target node (event name or `END`) |
| `session_idx` | Which visit produced this edge |

Toy size: 4 START edges + internal follows + 4 END edges.

---

## Function 2: `edge_table(edges)`

Aggregates instances into a compact map:

```python
groupby(from, to).size() → count
probability = count / sum(count for same from_activity)
```

Sorted by frequency so the strongest paths surface first.

| Column | Meaning |
|--------|---------|
| `from_activity` / `to_activity` | Edge |
| `count` | How many times observed |
| `probability` | Share of outbound edges from `from` |

**Highlighted toy edges:**

- `START → page_view`: count **4**, P **1.0** (every session starts that way)
- `page_view → scroll`: count **3**, P **0.75** (S2–S4; S1 goes to END instead)

---

## Function 3: `journey_variants(events)`

Shows one human-readable path per session.

### Collapse consecutive repeats

```python
keep[1:] = (session changes) OR (event_name changes)
```

If a session had `scroll → scroll → scroll`, it becomes a single `scroll` in the path string (cleaner variants). The toy has no consecutive repeats, so collapse is a no-op here.

### Path string

```
page_view > scroll > engaged_read > … > END
```

Toy variants:

| S | Journey |
|---|---------|
| 1 | `page_view > END` |
| 2 | `page_view > scroll > engaged_read > END` |
| 3 | `… > subscription_view > subscribe_click > END` |
| 4 | `… > checkout_start > payment_success > subscription_active > END` |

---

## `main()` outputs

| Section | Content |
|---------|---------|
| OUTPUT 1 | Event names per session |
| OUTPUT 2 | Raw edge instances |
| OUTPUT 3 | Aggregated DFG table + highlights |
| OUTPUT 4 | Journey variant strings |
| OUTPUT 5 | Acceptance checks (4 START→page_view, 4 variants) |

---

## DFG vs Funnel vs Markov

| | Grain | Nodes | Question |
|-|-------|-------|----------|
| Funnel | Session presence | Stages | Depth / cliffs |
| Markov | Consecutive steps | Stages + exit | Next-stage odds |
| **DFG** | Consecutive steps | **Event names** + START/END | Exact click paths |

Same visits, three lenses.

---

## What to take into the lab

On large data, DFG tables get huge. Lab code typically filters to top-N edges or activities. The toy shows the pure definition before filtering.
