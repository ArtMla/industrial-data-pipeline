# Architecture Decision Records

## ADR-001: XGBoost over LightGBM

**Status:** Accepted

**Context:** Both XGBoost and LightGBM achieve comparable accuracy on the AI4I 2020 dataset. A model format was needed that is both portable and trivially serialisable via boto3.

**Decision:** XGBoost's native `.json` export (`model.save_model("model.json")`) loads cleanly from a `tempfile` downloaded via `boto3.download_fileobj` — no additional serialisation layer, no pickle security concerns. LightGBM's `lgb.Booster` requires a text format that is less self-describing.

**Consequences:** XGBoost is the industry default in tabular ML. Its JSON format embeds feature names and hyperparameters, making S3-stored artifacts self-documenting. The `scale_pos_weight` parameter handles the 28:1 class imbalance without oversampling.

---

## ADR-002: FastAPI over Flask

**Status:** Accepted

**Context:** A lightweight REST API was needed to serve predictions and log results to PostgreSQL.

**Decision:** FastAPI was chosen for three reasons:
1. **Async DB writes** via asyncpg — prediction logging does not block the inference response
2. **Pydantic v2 validation** with `Field(ge=, le=)` — sensor reading bounds are enforced at the framework level, not in ad hoc `if` statements
3. **Auto-generated OpenAPI docs** at `/docs` — reviewers and clients can inspect and test the API without additional tooling

**Consequences:** Flask would require manual input validation and synchronous DB calls. FastAPI's startup lifespan (`@asynccontextmanager`) cleanly handles model loading from S3 and connection pool initialisation before the first request.

---

## ADR-003: Parquet over CSV in the Processed Data Lake

**Status:** Accepted

**Context:** The raw AI4I 2020 CSV (~500 KB, 10k rows) is small. Storage format is nonetheless a design decision with downstream effects.

**Decision:** AWS Glue writes Parquet with Snappy compression to `pred-maint-processed/features/`. Reasons:
- **70% storage reduction** vs CSV for this dataset's numeric columns
- **Predicate pushdown** — AWS Athena and `pandas.read_parquet` filter at the storage layer, not after reading all rows
- **Schema embedding** — column types and names are stored in the Parquet footer; downstream readers cannot silently misinterpret a float column as a string
- **Columnar reads** — training jobs that read only feature columns skip the target column entirely

**Consequences:** Local development requires `pyarrow` or `fastparquet`. The Glue job uses PySpark's built-in Parquet writer, which is already available in the Glue 4.0 runtime.

---

## ADR-004: S3-Based Model Registry over a Dedicated MLflow Tracking Server

**Status:** Accepted

**Context:** MLflow provides a model registry with versioning, stage transitions (Staging/Production), and a UI. Running it as a persistent server adds infrastructure cost.

**Decision:** Model artifacts are pushed directly to `s3://pred-maint-processed/models/xgb_{timestamp}.json` with a paired `_metrics.json`. MLflow is run locally via `docker-compose` for experiment tracking during development but is not deployed to AWS.

The active model key is written to `.model_version` on the training machine and set as the `MODEL_S3_KEY` environment variable for the API container.

**Consequences:** No MLflow server to maintain, patch, or pay for. The tradeoff is that stage promotion (Staging → Production) is manual — a `make deploy` command that updates the ECS task definition's `MODEL_S3_KEY` environment variable. For a portfolio project with infrequent model updates, this is acceptable and directly shows understanding of the cost/complexity tradeoff. A production system would warrant a managed MLflow server or SageMaker Model Registry.

---

## Security Note: RDS in a Public Subnet

This deployment places the RDS instance in a public subnet with a security group restricting inbound port 5432 to the developer's IP and the ECS task security group. This avoids the ~€30/month cost of a NAT Gateway.

**Tradeoff:** Not appropriate for data containing PII or regulated information. Acceptable for the AI4I 2020 public dataset used in this portfolio project.
