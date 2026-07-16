# Industrial Data Pipeline — Predictive Maintenance Platform

Production-grade ML pipeline for predicting machine failures in industrial environments, built on the [AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset). Portfolio project targeting Industrie 4.0 / industrial AI roles.

---

## Architecture Overview

```
Raw Data (CSV)
     │
     ▼
[1] S3 Ingestion (etl/upload_raw.py)     → s3://<raw-bucket>/ai4i/raw/
     │
     ▼
[2] AWS Glue ETL (etl/glue_job.py)       → CSV → validated Parquet → s3://<processed-bucket>/features/
     │
     ▼
[3] Feature Load (etl/load_features.py)  → Parquet + physics-informed features (ml/features.py) → PostgreSQL `features` table
     │
     ▼
[4] ML Training (ml/train.py)            → XGBoost: machine_failure + 5 failure-mode classifiers, MLflow tracking, S3 model registry
     │
     ▼
[5] FastAPI Service (api/)               → /predict, /health, /metrics — async PostgreSQL prediction log
     │
     ▼
[6] Containerisation                     → Docker + docker-compose (api, dashboard)
     │
     ▼
[7] Next.js Dashboard (dashboard/)       → KPI cards, prediction log, model metrics
     │
     ▼
[8] Infra & Ops (infra/, Makefile)       → S3/RDS/Glue/ECR setup scripts, cost-control (pause-rds/pause-ecs)
```

See `ARCHITECTURE.md` for the architecture decision records (XGBoost vs LightGBM, FastAPI vs Flask, Parquet vs CSV, S3 model registry vs MLflow server).

---

## Dataset

**AI4I 2020 Predictive Maintenance Dataset** — 10,000 samples, 14 features.

| Feature | Description |
|---|---|
| Type | Product quality variant (L / M / H) |
| Air temperature [K] | Ambient air temperature |
| Process temperature [K] | Process temperature |
| Rotational speed [rpm] | Spindle speed |
| Torque [Nm] | Applied torque |
| Tool wear [min] | Cumulative tool wear time |

**Targets:** Machine failure (binary) + failure modes: TWF, HDF, PWF, OSF, RNF.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Storage | AWS S3 |
| ETL | AWS Glue (PySpark), pandera schema validation |
| Database | PostgreSQL (RDS) |
| ML | Python, XGBoost, scikit-learn, MLflow |
| API | FastAPI, asyncpg |
| Frontend | Next.js |
| Infra | Docker, AWS ECS/ECR |
| Testing | pytest |

---

## Project Status

| Step | Status |
|---|---|
| Dataset acquired | Done |
| S3 ingestion + schema validation | Done |
| Glue ETL (CSV → Parquet) | Done |
| Feature load (PostgreSQL) | Done |
| XGBoost training — machine_failure | Done |
| XGBoost training — 5 failure-mode classifiers | Done |
| FastAPI inference service | Done (serves machine_failure plus the 5 real per-mode models via `models/manifest_{version}.json`) |
| Docker + docker-compose | Done |
| Next.js dashboard | Done |
| AWS infra setup scripts (S3/RDS/Glue/ECR) | Done |
| GitHub Actions CI/CD | Pending |

---

## Getting Started

```bash
# Install Python dependencies
pip install -e .   # or: pip install -r api/requirements.txt, plus xgboost, mlflow, pandera, boto3, psycopg2

# Configure environment
cp .env.example .env   # fill in AWS credentials, S3 buckets, DATABASE_URL

make setup                # copies .env, prints the schema.sql command to run
make upload-raw            # data/raw/ai4i2020.csv -> S3 raw bucket
make validate-schema       # pandera validation of the local CSV
make run-glue               # trigger the Glue ETL job (CSV -> Parquet)
make load-features          # Parquet -> PostgreSQL features table
make train                  # train XGBoost models, push to S3, log to MLflow
make api                    # FastAPI dev server on :8000
make dashboard               # Next.js dev server on :3000
make test                   # pytest suite
```

See `make help` for the full command list, and `infra/README.md` for one-time AWS resource setup.

---

## Author

Arthur Mlambo — MSc Data Science | Mechatronics Engineering background  
[GitHub](https://github.com/ArtMla)
