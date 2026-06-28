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

Creates:
- `pred-maint-raw` — immutable landing zone for source CSV
- `pred-maint-processed` — Parquet features + versioned model artifacts

---

## 3. AWS Glue IAM Role

Glue needs a role with two policies. Do this in the Console before running `setup_glue.py`.

**Step-by-step:**

1. IAM → Roles → Create role
2. Trusted entity: **AWS service** → Glue
3. Attach managed policy: `AWSGlueServiceRole`
4. Create an inline policy (JSON):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::pred-maint-raw",
        "arn:aws:s3:::pred-maint-raw/*",
        "arn:aws:s3:::pred-maint-processed",
        "arn:aws:s3:::pred-maint-processed/*"
      ]
    }
  ]
}
```

5. Name the role: `AWSGlueServiceRole-PredMaint`
6. Copy the role ARN and set:

```bash
export GLUE_ROLE_ARN=arn:aws:iam::<account-id>:role/AWSGlueServiceRole-PredMaint
```

Then register the Glue job:

```bash
python infra/setup_glue.py
```

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
