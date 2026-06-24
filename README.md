# Industrial Data Pipeline — Predictive Maintenance Platform

Production-grade ML pipeline for predicting machine failures in industrial environments, built on the [AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset). Portfolio project targeting Industrie 4.0 / industrial AI roles.

---

## Architecture Overview

```
Raw Data (CSV)
     │
     ▼
[1] S3 Ingestion          → s3://mlambo-industrial-data-2026/raw/
     │
     ▼
[2] Data Pipeline         → Load & validate into PostgreSQL (local → AWS RDS)
     │
     ▼
[3] Feature Engineering   → Sensor-derived features, failure mode labels
     │
     ▼
[4] ML Model (XGBoost)    → Binary failure prediction + 5 failure mode classifiers
     │
     ▼
[5] FastAPI Service        → REST endpoints for real-time inference
     │
     ▼
[6] Containerisation       → Docker + AWS ECR/ECS deployment
     │
     ▼
[7] Frontend Dashboard     → Next.js UI showing live predictions & sensor trends
     │
     ▼
[8] CI/CD + Monitoring     → GitHub Actions, AWS CloudWatch
```

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
| Database | PostgreSQL → AWS RDS |
| ML | Python, XGBoost, scikit-learn |
| API | FastAPI |
| Frontend | Next.js |
| Infra | Docker, AWS ECS/ECR |
| CI/CD | GitHub Actions |
| Monitoring | AWS CloudWatch |

---

## Project Status

| Step | Status |
|---|---|
| Dataset acquired | Done |
| S3 ingestion script | Done |
| Data pipeline (S3 → PostgreSQL) | Done |
| Feature engineering | In progress |
| XGBoost model training | Pending |
| FastAPI inference service | Pending |
| Docker + ECS deployment | Pending |
| Next.js dashboard | Pending |
| GitHub Actions CI/CD | Pending |

---

## Getting Started

```bash
# Install dependencies
pip install boto3 python-dotenv

# Configure environment
cp .env.example .env   # fill in AWS credentials and bucket name

# Upload raw data to S3
python scripts/upload_to_s3.py
```

---

## Author

Arthur Mlambo — MSc Data Science | Mechatronics Engineering background  
[GitHub](https://github.com/ArtMla)
