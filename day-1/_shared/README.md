# `_shared/` — toy data for Day 1 examples

This folder is the **small teaching dataset** used by every `examples/` script.

It is **not** the full lab clickstream (`day-1/data/web_events.csv`). Think whiteboard-sized stories you can check by hand.

## What’s in this folder

```text
day-1/_shared/
├── README.md                 ← this file
├── generate_toy_data.py      ← rebuilds the CSVs
├── toy_raw_events.py         ← loader for sessionize
├── toy_sessions.py           ← loader for journey / HMM / features
└── data/
    ├── README.md
    ├── toy_raw_events.csv    ← raw clicks (no session yet)
    ├── toy_sessions.csv      ← already cut into 4 visits
    └── toy_audience.csv      ← 12 cookies for clustering
```

| Piece | Role |
|-------|------|
| `data/*.csv` | The actual toy tables (what examples read) |
| `generate_toy_data.py` | Source of truth → writes the three CSVs |
| `toy_raw_events.py` | `load_raw_events()` + `describe_raw()` |
| `toy_sessions.py` | `load_toy_events()` + stage map + `describe_sessions()` |

## Regenerate

```bash
python day-1/_shared/generate_toy_data.py
```

After that, examples can run without touching `day-1/data/`.

---

## Big picture (which toy for which example)

```text
toy_raw_events.csv  ──►  01_sessionize example
                         (prove 30-min cut + 2s dedupe)

toy_sessions.csv    ──►  Funnel / Markov / DFG / HMM / Features
                         (prove journey + modes + user vectors)

toy_audience.csv    ──►  Segmentation example
                         (prove K-Means / GMM recover 3 groups)
```

| Need | File | Why this shape |
|------|------|----------------|
| Prove session rules | `toy_raw_events.csv` | Has a duplicate and a 35‑min gap |
| Prove Funnel / Markov / DFG / HMM / features | `toy_sessions.csv` | Four finished visits, already staged |
| Prove clustering | `toy_audience.csv` | 12 points in 3 planted personas |

---

## `data/toy_raw_events.csv`

**Question it answers:** What do clicks look like *before* sessionization?

**Used by:** `01_sessionize/examples/01_sessionize_example.py` via `load_raw_events()`.

### Columns

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Cookie / visitor |
| `timestamp` | Event time |
| `event_name` | Action (`page_view`, `scroll`, …) |
| `content_id` | Article key (used in near-duplicate check) |
| `device_type` | desktop / mobile / tablet |
| `referrer` | First-touch source (often blank later) |

There is **no** `session_id` here — the sessionize example creates it.

### Cookie stories (designed quirks)

| Cookie | What happens | What you should see |
|--------|----------------|---------------------|
| **A0001** | page_view, **duplicate** +1s, scroll +5m, page_view **+35m** | Drop dup; **2 sessions** (30‑min rule) |
| **A0002** | page_view → scroll → engaged_read | One engaged visit |
| **A0003** | … → subscription_view → subscribe_click | Intent path, no convert |
| **A0004** | … → checkout → payment → `subscription_active` | Deep path + conversion |

---

## `data/toy_sessions.csv`

**Question it answers:** What do four clean visits look like for journey math?

**Used by:** Funnel, Markov, DFG, HMM, Features examples via `load_toy_events()`.

### Columns

| Column | Meaning |
|--------|---------|
| `session_idx` | Visit id `1…4` |
| `timestamp` | Event time |
| `event_name` | Raw action |
| `anonymous_id` | `A0001`…`A0004` (one cookie per visit in this toy) |
| `stage` | Funnel tag (`landing` … `subscription`) |

### Visit stories

| Session | Path | Teaching role |
|---------|------|----------------|
| **S1** | `page_view` only | Bounce |
| **S2** | → `engaged_read` | Engaged exit |
| **S3** | → `subscribe_click` | Intent cliff (no checkout) |
| **S4** | → `subscription_active` | Full convert path |

Stage map used by the loader (same ladder as the lab):

`landing → scroll → engaged → intent → deep → registration → subscription`

---

## `data/toy_audience.csv`

**Question it answers:** Can clustering recover three obvious audience types?

**Used by:** `05_segmentation/examples/01_segmentation_example.py` via `toy_audience()`.

### Columns

| Column | Meaning |
|--------|---------|
| `anonymous_id` | Cookie id (`B*`, `R*`, `C*`) |
| `persona` | Planted truth label (**not** fed into the model) |
| `n_sessions` | How often they visit |
| `mean_duration_sec` | Typical visit length |
| `mean_furthest_rank` | Typical depth (1=landing … 5=deep) |
| `share_intent` / `share_deep` | Mix of deeper visits |
| `subscription_view_rate` | How often they see plans |
| `conversion_rate` | How often visits convert |

### Planted groups (4 cookies each)

| Persona | Pattern | Expect label |
|---------|---------|--------------|
| `bouncer_truth` (B1–B4) | 1 short shallow visit, no convert | `bouncers` |
| `reader_truth` (R1–R4) | More sessions, mid depth, little intent | `regular_readers` |
| `converter_truth` (C1–C4) | Deep + intent + high conversion | `converters` |

`persona` is only for checking answers. Clustering uses the numeric feature columns.

---

## Loader modules (Python)

### `toy_raw_events.py`

| Function | Job |
|----------|-----|
| `load_raw_events()` | Read `data/toy_raw_events.csv`, parse timestamps |
| `describe_raw()` | Print the cookie stories at the start of the example |

### `toy_sessions.py`

| Name | Job |
|------|-----|
| `STAGE_BY_EVENT` | Event → funnel stage map |
| `FUNNEL_STAGES` | Ordered ladder for Funnel / Markov |
| `load_toy_events()` | Read `data/toy_sessions.csv`, ensure stage / cookie |
| `describe_sessions()` | Print the four visit stories |

### `generate_toy_data.py`

Hand-authored rows in Python → writes all three CSVs under `data/`.  
Edit this script when you want to change the toys, then regenerate.

---

## How examples find this folder

Each example adds `_shared` to `sys.path` and imports the loaders:

```text
day-1/<step>/examples/*.py
        │
        └── parents[2] = day-1/
                └── _shared/   ← import toy_raw_events / toy_sessions
                        └── data/*.csv
```

Segmentation reads `data/toy_audience.csv` directly (same folder).

---

## vs full lab data

| | `_shared/data/` (examples) | `day-1/data/` (full lab) |
|--|----------------------------|---------------------------|
| Size | Dozens of rows | Millions of clicks (Git LFS) |
| Purpose | Hand-check algorithms | Real pipeline run |
| Session id | Built by sessionize toy, or already present in `toy_sessions` | Built by `step01_sessionize.py` |

---

## Teaching takeaway

`_shared` answers: *“Show me a tiny dataset where every rule is obvious.”*  
Full lab data answers: *“Now run the same ideas at scale.”*
