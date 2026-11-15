# Day 1 algorithm examples

Tiny, hand-checkable demos for Journey, HMM, Features, and Segmentation.

They use **toy data** (not full `web_events.csv`) so you can verify logic on a whiteboard.

## Setup

```bash
conda activate awsproject
cd /path/to/CONSUMERANALYTICS
```

## Run all

```bash
python day-1/examples/01_funnel_example.py
python day-1/examples/02_markov_example.py
python day-1/examples/03_dfg_example.py
python day-1/examples/04_hmm_example.py
python day-1/examples/05_feature_engineering_example.py
python day-1/examples/06_segmentation_example.py
```

## What each example teaches

| File | Step | Algorithm | Question |
|------|------|-----------|----------|
| `01_funnel_example.py` | Journey | Funnel | How many sessions reached each stage? |
| `02_markov_example.py` | Journey | Markov (+ exit) | Given this stage, what happens next? |
| `03_dfg_example.py` | Journey | DFG | What event→event paths occur? |
| `04_hmm_example.py` | State modeling | Categorical HMM | What latent reading mode is active? |
| `05_feature_engineering_example.py` | Features | Session→user rollup | How do visits become cookie features? |
| `06_segmentation_example.py` | Segmentation | K-Means + GMM | Which audience group is this cookie? |

Shared Journey/HMM/Features data: `toy_sessions.py`  
Segmentation uses a separate 12-cookie toy audience (3 clear personas).

## Journey toy sessions

| Session | Path idea |
|---------|-----------|
| S1 | Bounce on `page_view` |
| S2 | Read to `engaged_read`, then leave |
| S3 | Reach intent, no checkout |
| S4 | Intent → checkout → payment → subscribe |

## How the later steps connect

```
Events
  → Funnel / Markov / DFG   (observed journey)
  → HMM                     (latent modes inside sequences)
  → Feature engineering     (session → user vectors)
  → K-Means / GMM           (audience segments)
```
