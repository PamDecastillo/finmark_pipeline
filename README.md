# FinMark Data Pipeline
**Course:** MO-IT151 | Platform Technologies  
**Group:** 5 A3101  
**Members:**
- Maria Chesam Leonor
- Christen Amiel Ongleo
- Pamela Loraine Decastillo
- Stephen Dave Campillanes

---

## Project Overview
This project builds a data analytics pipeline for FinMark Corporation
to replace their outdated batch-processing system with a cleaned,
validated, and transformed data pipeline.

---

## Project Structure
finmark_pipeline/

├── config/

│   ├── .env

│   └── pipeline_config.yaml

├── data/

│   ├── raw/

│   ├── cleaned/

│   └── processed/

├── docs/

│   └── MILESTONE2_DOCUMENTATION.md

├── logs/

│   └── pipeline_run.log

├── scripts/

│   ├── clean_data.py

│   ├── transform_data.py

│   └── run_pipeline.py

├── finmark_analysis.ipynb

└── requirements.txt

---

## How to Run

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Full Pipeline
```bash
python scripts/run_pipeline.py
```

### Run Individual Steps
```bash
python scripts/clean_data.py
python scripts/transform_data.py
```

### Open Jupyter Notebook
```bash
python -m notebook
```
Then open `finmark_analysis.ipynb`

---

## What Each Script Does

| Script | What it does |
|---|---|
| `clean_data.py` | Removes junk columns, handles nulls, masks user IDs, validates schema |
| `transform_data.py` | Computes KPIs, builds funnel, adds growth flags |
| `run_pipeline.py` | Runs both scripts in order automatically |

---

## Output Files

| File | Rows | Description |
|---|---|---|
| `data/cleaned/trend_report_cleaned.csv` | 20 | Weekly trend data cleaned |
| `data/cleaned/marketing_summary_cleaned.csv` | 100 | Daily marketing data cleaned |
| `data/cleaned/event_logs_cleaned.csv` | 1,787 | Event logs deduplicated and masked |
| `data/processed/marketing_kpis.csv` | 100 | Sales KPIs and anomaly flags |
| `data/processed/event_funnel_daily.csv` | 6 | Daily conversion funnel |
| `data/processed/trend_report_processed.csv` | 20 | Growth flags added |

---

## Pipeline Stages

| Stage | Layer | Description |
|---|---|---|
| Data Cleaning | L0 | Remove nulls, duplicates, junk columns |
| PII Masking | L1 | SHA-256 hash user IDs |
| Schema Validation | L2 | Pandera type and range checks |
| Session Correlation | L3 | Link events to marketing data by date |
| KPI Computation | L4 | Sales per user, 7-day average, conversion rate |

---

## Tools Used
- **Python 3.14**
- **Pandas** — data cleaning and transformation
- **Pandera** — schema validation
- **Jupyter Notebook** — interactive analysis
- **Git & GitHub** — version control

