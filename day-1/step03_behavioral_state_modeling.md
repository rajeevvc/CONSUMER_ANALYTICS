# Learner guide — Behavioral state modeling (`step03_behavioral_state_modeling.py`)

## Goal

Fit a **categorical Hidden Markov Model (HMM)** on click sequences to recover **latent reading modes** (e.g. skimming, scrolling, exploring, deep_reading). Label every browsing event with the most likely mode.

This is **not** the same as funnel stage tags: stages are rules you define; HMM modes are **inferred** from sequences.

HSMM (explicit duration) is optional; this lab uses a standard HMM where duration is **geometric** via self-transitions.

## How to run

```bash
conda activate awsproject
python day-1/step01_sessionize.py                    # prerequisite
python day-1/step03_behavioral_state_modeling.py
```

Needs `hmmlearn` (vendored under `marketing-behavioral-labs/day1/.vendor` if not installed in the env).

## Input

| File | Required columns |
|------|------------------|
| `day-1/output/sessionized_events.csv` | `anonymous_id`, `timestamp`, `event_name`, `session_idx` |

## What you must implement

1. **Encode observations** — map each `event_name` to integer `obs` via a fixed vocabulary list  
2. **Exclude conversions** from train/decode (`register_complete`, `subscription_active`)  
3. **Train window** — `timestamp < 2026-03-01`  
4. **Sample** — e.g. ≤ 8000 sessions, ≤ 25 events each (for speed)  
5. **Fit** `CategoricalHMM` with ~4 states; multiple random restarts; keep a balanced high-likelihood model  
6. **Name states** — match emission mass to mode profiles; fallback names if mixed  
7. **Decode** — Viterbi (`predict`) mode for every behavior event  
8. **Report** — emissions, geometric durations, mode transitions, reader-level dominant modes  

### Suggested mode profiles (for naming)

| Mode | Typical events |
|------|----------------|
| skimming | `page_view`, `login` |
| scrolling | `scroll` |
| exploring | `engaged_read`, `share` |
| deep_reading | plan/checkout/register_start family |

## Output

| File | Content |
|------|---------|
| `day-1/output/hmm_modes.csv` | Mode emissions / start / mean sojourn |
| `day-1/output/hmm_durations.csv` | Geometric duration probabilities |
| `day-1/output/hmm_mode_transitions.csv` | Mode→mode transitions |
| `day-1/output/hmm_reader_modes.csv` | Dominant-mode audience mix |
| `day-1/output/sessionized_events_hmm.csv` | Events + `hmm_state`, `hmm_mode` |

## Acceptance checks

- Conversion events have no mode (or empty / -1)  
- Every behavior event has an `hmm_mode`  
- Feature engineering can optionally join HMM shares from `sessionized_events_hmm.csv`  

## Teaching takeaway

Answer: *“What reading mode is happening inside this visit?”* (sequence / latent state)
