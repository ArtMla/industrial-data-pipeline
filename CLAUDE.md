# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Portfolio project: an industrial predictive-maintenance data pipeline built on the AI4I 2020 dataset (`data/raw/ai4i2020.csv`). Currently implements the data-ingestion and feature-engineering stages of a larger planned architecture (S3 → PostgreSQL → feature engineering → XGBoost model → FastAPI service → Docker/ECS → Next.js dashboard → CI/CD). See README.md "Architecture Overview" and "Project Status" for the full roadmap and what's actually built vs. pending.

## Commands

No dependency manifest exists yet (no requirements.txt/pyproject.toml). Install ad hoc:

```bash
pip install boto3 python-dotenv pandas sqlalchemy psycopg2-binary scikit-learn xgboost joblib
```

Set up environment (never commit `.env`):

```bash
cp .env.example .env   # fill in AWS credentials, S3 bucket, PostgreSQL connection
```

Run the pipeline stages in order:

```bash
python scripts/upload_to_s3.py        # data/raw/ai4i2020.csv -> s3://<bucket>/raw/ai4i2020.csv
python scripts/load_to_postgres.py    # S3 -> validate -> sensor_readings table
python scripts/feature_engineering.py # sensor_readings -> engineered features -> sensor_features table
python scripts/train_model.py         # sensor_features -> models/xgb_*.joblib + models/metrics.csv
```

There is no test suite, linter, or build step in this repo yet.

## Architecture

Each script in `scripts/` is a standalone, sequential ETL stage — there's no shared library or orchestrator (no Airflow/Prefect/Dagster yet). Each script loads its own `.env` via `python-dotenv` and connects independently.

- **`upload_to_s3.py`** — uploads the raw CSV to S3 at a fixed key (`raw/ai4i2020.csv`).
- **`load_to_postgres.py`** — fetches the CSV from S3, validates it against `EXPECTED_COLUMNS` (raises on missing columns, nulls, or unexpected `Type` values), renames columns to snake_case, and writes to the `sensor_readings` table (full `if_exists="replace"` on every run — not incremental).
- **`feature_engineering.py`** — reads `sensor_readings` from PostgreSQL, derives features (`temp_delta_k`, `power_w`, `tool_wear_torque`, `tool_wear_speed`, `torque_speed_ratio`) and writes `sensor_features` (also `if_exists="replace"`).

Column naming convention: source CSV uses human-readable names with units (`Air temperature [K]`); DB tables use snake_case with unit suffixes (`air_temp_k`). When adding a new stage, follow this same rename-at-load pattern rather than carrying raw CSV column names into the database.

Both DB-writing scripts build the SQLAlchemy engine from individual `DB_*` env vars (not a single `DATABASE_URL`) and each script defines its own `CREATE_TABLE_SQL` inline (`CREATE TABLE IF NOT EXISTS`) rather than using migrations.

Target labels carried through every stage: `machine_failure` (binary) plus five failure-mode flags `twf`, `hdf`, `pwf`, `osf`, `rnf`.
