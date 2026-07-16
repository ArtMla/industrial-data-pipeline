# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Portfolio project: a production-shaped industrial predictive-maintenance platform built on the AI4I 2020 dataset (`data/raw/ai4i2020.csv`). Full pipeline implemented: S3 ingestion → AWS Glue ETL → PostgreSQL feature store → XGBoost training (MLflow-tracked, S3 model registry) → FastAPI inference service → Next.js dashboard → Docker/infra setup scripts. See README.md "Architecture Overview" and "Project Status" for what's built vs. pending (CI/CD is the main gap).

Earlier in this project's history a simpler `scripts/` pipeline (CSV → S3 → PostgreSQL → feature engineering, no API/dashboard/infra) was built in parallel with this one on a different branch/session. It has been removed — this tree (`etl/`, `ml/`, `api/`, `dashboard/`, `infra/`) is canonical.

## Commands

```bash
pip install -e .   # pyproject.toml; or install api/requirements.txt plus xgboost, mlflow, pandera, boto3, psycopg2
```

Set up environment (never commit `.env`):

```bash
cp .env.example .env   # fill in AWS credentials, S3 buckets, DATABASE_URL, MLFLOW_TRACKING_URI
```

Run the pipeline stages in order (see `Makefile` for the full list):

```bash
make upload-raw        # data/raw/ai4i2020.csv -> S3 raw bucket (etl/upload_raw.py)
make validate-schema   # pandera validation of the local CSV (etl/validate_schema.py)
make run-glue          # trigger AWS Glue job: CSV -> validated Parquet (etl/glue_job.py, PySpark, AWS-only)
make load-features     # Parquet -> PostgreSQL `features` table, adds physics-informed features (etl/load_features.py)
make train             # train XGBoost models, push to S3, log to MLflow (ml/train.py)
make api                # FastAPI dev server on :8000
make dashboard          # Next.js dev server on :3000
make test                # pytest suite (tests/)
make lint                # ruff
```

## Architecture

- **`etl/`** — ingestion and transform. `upload_raw.py` pushes the CSV to S3 (embeds an MD5 checksum in object metadata). `validate_schema.py` runs a `pandera` schema against the local CSV (column types + physical value ranges) before upload. `glue_job.py` is an AWS Glue PySpark job — CSV → snake_case-renamed, range-filtered, Parquet (only runs inside Glue, not locally). `load_features.py` reads that Parquet from S3, adds engineered features via `ml/features.py`, and bulk-inserts (`TRUNCATE` + `execute_values`) into the PostgreSQL `features` table.
- **`ml/features.py`** — pure functions (no I/O): `temp_diff`, `mechanical_power`, `wear_rate`, `overstrain_flag`, plus `build_feature_matrix` for single-row inference. Imported identically by `ml/train.py` and `api/router.py` so train-time and serve-time feature logic can't drift apart — always change both call sites' behavior together by editing this one module.
- **`ml/train.py`** — trains 6 separate XGBoost binary classifiers: `machine_failure` (primary) plus `twf`/`hdf`/`pwf`/`osf`/`rnf` (each has a distinct physical driver, so no shared multi-label model). `scale_pos_weight` is computed per-target from the actual train-split class ratio. Each model + its metrics.json is pushed to S3 under `models/`; `machine_failure` keeps the unsuffixed `xgb_{version}.json` key for backward compatibility with `api/model_loader.py`'s `MODEL_S3_KEY`, the 5 failure-mode models use `xgb_{target}_{version}.json`. A `models/manifest_{version}.json` maps all 6 target → S3 key. MLflow logs one run per target under experiment `pred-maint-xgboost`.
- **`ml/evaluate.py`** — precision/recall/F1/AUC-ROC + a confusion-matrix PNG per target (`docs/confusion_matrix_{target}.png`).
- **`api/`** — FastAPI service. `model_loader.py` downloads the primary model at `MODEL_S3_KEY` from S3 at startup, then derives that version's `models/manifest_{version}.json` key and loads the 5 real `twf`/`hdf`/`pwf`/`osf`/`rnf` models it points to (singleton, all 6 held in memory). `ModelLoader.predict()` returns each failure mode's probability from its own trained model; if a target is missing from the manifest (e.g. `MODEL_S3_KEY` points at a version trained before per-mode models existed), it falls back to the primary probability scaled by fixed historical ratios (0.18/0.27/0.31/0.21/0.03) for that target only, with a startup warning logged.
- **`dashboard/`** — Next.js UI (KPI cards, prediction log, model metrics) reading from the FastAPI service.
- **`infra/`** — one-time AWS resource setup scripts (S3, RDS, Glue, ECR) — see `infra/README.md`.
- **`tests/`** — pytest suite covering ETL, API, and feature functions.

Column naming convention: source CSV uses human-readable names with units (`Air temperature [K]`); everything downstream uses snake_case (`air_temp`, no unit suffix in this tree — differs from the removed `scripts/` tree's `air_temp_k` convention).

Target labels carried through the pipeline: `machine_failure` (binary) plus five failure-mode flags `twf`, `hdf`, `pwf`, `osf`, `rnf` — all now present in the `features` table (`infra/schema.sql`) and loaded by `etl/load_features.py`.

See `ARCHITECTURE.md` for ADRs (XGBoost vs LightGBM, FastAPI vs Flask, Parquet vs CSV, S3 model registry vs MLflow server, RDS public-subnet tradeoff).
