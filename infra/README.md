# AWS Infrastructure Setup

## 1. Prerequisites

```bash
pip install boto3
aws configure   # set Access Key, Secret, Region (eu-central-1)
```

## 2. S3 Buckets

```bash
python infra/setup_s3.py
```

Named via `AWS_S3_RAW_BUCKET` / `AWS_S3_PROCESSED_BUCKET` in `.env`. This project uses a
single existing bucket, `mlambo-industrial-data-2026`, for both — set both env vars to
that name and skip `setup_s3.py` (the bucket already exists):
- raw data — immutable landing zone for source CSV (`ai4i/raw/ai4i2020.csv`)
- processed data — Parquet features (`features/`) + versioned model artifacts (`models/`)

Raw and processed objects live under different key prefixes in the same bucket, so
there's no collision.

---

## 3. AWS Glue Job Setup (resume here)

Status as of last session: raw CSV uploaded to
`s3://mlambo-industrial-data-2026/ai4i/raw/ai4i2020.csv` (`make upload-raw`), schema
validated locally (`make validate-schema`). Glue IAM role and job registration are
still pending — do these steps in order:

**3a. Create the Glue IAM role (Console)**

1. IAM → Roles → Create role
2. Trusted entity: **AWS service** → Glue
3. Attach managed policy: `AWSGlueServiceRole`
4. Create an inline policy (JSON). This project uses a single bucket
   (`mlambo-industrial-data-2026`) for both raw and processed data:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::mlambo-industrial-data-2026",
        "arn:aws:s3:::mlambo-industrial-data-2026/*"
      ]
    }
  ]
}
```

5. Name the role: `AWSGlueServiceRole-PredMaint`
6. Copy the role ARN (format: `arn:aws:iam::<account-id>:role/AWSGlueServiceRole-PredMaint`)

**3b. Set `GLUE_ROLE_ARN` in `.env`**

Edit `.env` and replace the placeholder value with the real ARN from step 3a6:

```
GLUE_ROLE_ARN=arn:aws:iam::<account-id>:role/AWSGlueServiceRole-PredMaint
```

**3c. Register the Glue job**

`infra/setup_glue.py` is run directly (not via `make`), so it doesn't get `.env`
auto-loaded the way `make` targets do — export it into the shell first:

```bash
set -a; source .env; set +a
python infra/setup_glue.py
```

This uploads `etl/glue_job.py` to `s3://mlambo-industrial-data-2026/glue-scripts/` and
registers/re-registers the `pred-maint-etl` job (idempotent — safe to re-run after
editing `etl/glue_job.py`).

**3d. Run it**

```bash
make run-glue
```

This calls `aws glue start-job-run --job-name pred-maint-etl` (uses `aws configure`
credentials from step 1, not `.env`). Job reads
`s3://mlambo-industrial-data-2026/ai4i/raw/ai4i2020.csv`, validates/renames columns, and
writes Parquet to `s3://mlambo-industrial-data-2026/features/`.

**3e. Check status**

Console: AWS Glue → ETL jobs → `pred-maint-etl` → Runs tab. Or:

```bash
aws glue get-job-runs --job-name pred-maint-etl --max-results 1
```

Once it succeeds, confirm output exists:

```bash
aws s3 ls s3://mlambo-industrial-data-2026/features/
```

Then continue with `make load-features`.

---

## 4. RDS PostgreSQL

See `infra/setup_rds.py` for Console instructions (recommended) or boto3 automation.

After creation, apply the schema:

```bash
psql $DATABASE_URL -f infra/schema.sql
```

**Cost control:**

```bash
make pause-rds    # stop the instance when not in use
```

---

## 5. ECR Repositories

```bash
python infra/setup_ecr.py
```

Then add the printed values to GitHub → Settings → Secrets → Actions:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key (read-only ECR + ECS permissions) |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |
| `AWS_REGION` | `eu-central-1` |
| `ECR_REGISTRY` | `<account-id>.dkr.ecr.eu-central-1.amazonaws.com` |
| `ECR_REPOSITORY_API` | `pred-maint-api` |
| `ECR_REPOSITORY_DASHBOARD` | `pred-maint-dashboard` |
| `DATABASE_URL` | Full PostgreSQL connection string |
| `MODEL_S3_KEY` | e.g. `models/xgb_20240101_120000.json` |

---

## 6. ECS Fargate (optional — for live demo)

1. Create a cluster: `pred-maint-cluster`
2. Register task definitions for `api` and `dashboard` referencing ECR image URIs
3. Create services with desired count 1

```bash
make pause-ecs    # set desired count to 0 when not demoing
```

---

## Estimated Monthly Cost

| Service | Config | Cost |
|---|---|---|
| S3 | ~50 MB, two buckets | ~€0.001 |
| Glue | 1 DPU × 5 min, run once | ~€0.04/run |
| RDS t3.micro | Free tier (first 12 months) | €0 → ~€15 |
| ECR | 2 images ~300 MB | ~€0 |
| ECS Fargate | 0.25 vCPU / 0.5 GB, paused when idle | ~€0.01/hr active |
| CloudFront | Free tier | €0 |
