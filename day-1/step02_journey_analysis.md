# Learner guide — Journey analysis (`step02_journey_analysis.py`)

## Goal

From sessionized events, build three complementary journey views:

| Method | Question | Unit |
|--------|----------|------|
| **Funnel** | How many sessions reach each stage? Advance rate? | Stage |
| **Markov** | Given current stage, where next (or exit)? | Stage + `exit` |
| **DFG** | What event→event paths actually happen? | Event name |

## How to run

```bash
conda activate awsproject
python day-1/step01_sessionize.py          # if not already done
python day-1/step02_journey_analysis.py
```

### Tiny worked examples (Funnel / Markov / DFG)

```bash
python day-1/examples/01_journey/01_funnel_example.py
python day-1/examples/01_journey/02_markov_example.py
python day-1/examples/01_journey/03_dfg_example.py
```

See [examples/README.md](examples/README.md).

## Input

| File | Required columns |
|------|------------------|
| `day-1/output/sessionized_events.csv` | `anonymous_id`, `timestamp`, `event_name`, `session_idx` |

If missing, rebuild sessions from `day-1/data/web_events.csv`.

## What you must implement

### Shared prep
- Retag `event_name` → `stage` with the same ladder as sessionize (`landing`…`deep`, registration, subscription)  
- Flag conversion events  

### Funnel
For each stage in order:
- event count  
- sessions containing the stage  
- sessions whose furthest stage is here  
- advance rate = share that also contain the **next** stage  

### Markov (train on `timestamp < 2026-03-01`)
- States = funnel stages + synthetic **`exit`**  
- Count consecutive stage→stage transitions within a session  
- Last event of session → transition to `exit`  
- Row-normalize to probabilities  
- Report drop-off (exit probability) per stage  

### DFG / process map (same pre-March window)
- Build directly-follows on **`event_name`** (not stages): `START → … → END`  
- Edge counts, probabilities, simple dependency  
- Activity stats, self/return loops  
- Top journey variants (collapse consecutive repeats; cap path length)  

## Output

| File | Content |
|------|---------|
| `day-1/output/funnel.csv` | Stage funnel + advance rates |
| `day-1/output/markov_transitions.csv` | Long-form transitions |
| `day-1/output/markov_transition_matrix.csv` | Wide probability matrix |
| `day-1/output/markov_dropoff.csv` | Exit probability by stage |
| `day-1/output/dfg_activities.csv` | Event node stats |
| `day-1/output/dfg_edges.csv` | Event→event edges |
| `day-1/output/dfg_loops.csv` | Loops |
| `day-1/output/dfg_journeys.csv` | Top path variants |

## Acceptance checks

- Funnel / Markov use **stages**; DFG uses **event names**  
- Intent → deep advance should be much lower than earlier steps (cliff)  
- Markov matrix rows roughly sum to 1  

## Teaching takeaway

Funnel = reach; Markov = next-step odds; DFG = fine-grained click map.
