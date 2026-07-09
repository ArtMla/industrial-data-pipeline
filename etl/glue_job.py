"""
AWS Glue PySpark ETL job: AI4I 2020 CSV → validated snappy Parquet.

Reads from:  s3://{RAW_BUCKET}/ai4i/raw/ai4i2020.csv
Writes to:   s3://{PROCESSED_BUCKET}/features/

Job arguments (configured in infra/setup_glue.py):
  --RAW_BUCKET, --PROCESSED_BUCKET
"""
import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import BooleanType, FloatType, IntegerType

args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_BUCKET", "PROCESSED_BUCKET"])
RAW_BUCKET = args["RAW_BUCKET"]
PROCESSED_BUCKET = args["PROCESSED_BUCKET"]

sc = SparkContext()
spark = SparkSession(sc)

# ── 1. Ingest ──────────────────────────────────────────────────────────────────
raw_path = f"s3://{RAW_BUCKET}/ai4i/raw/ai4i2020.csv"
df = spark.read.option("header", "true").option("inferSchema", "true").csv(raw_path)
print(f"Rows ingested: {df.count():,}")

# ── 2. Rename columns to snake_case ────────────────────────────────────────────
renames = {
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "product_type",
    "Air temperature [K]": "air_temp",
    "Process temperature [K]": "process_temp",
    "Rotational speed [rpm]": "rotational_speed",
    "Torque [Nm]": "torque",
    "Tool wear [min]": "tool_wear",
    "Machine failure": "machine_failure",
    "TWF": "twf",
    "HDF": "hdf",
    "PWF": "pwf",
    "OSF": "osf",
    "RNF": "rnf",
}
for old, new in renames.items():
    if old in df.columns:
        df = df.withColumnRenamed(old, new)

# ── 3. Cast to correct types ───────────────────────────────────────────────────
df = (
    df.withColumn("udi", F.col("udi").cast(IntegerType()))
    .withColumn("air_temp", F.col("air_temp").cast(FloatType()))
    .withColumn("process_temp", F.col("process_temp").cast(FloatType()))
    .withColumn("rotational_speed", F.col("rotational_speed").cast(IntegerType()))
    .withColumn("torque", F.col("torque").cast(FloatType()))
    .withColumn("tool_wear", F.col("tool_wear").cast(IntegerType()))
    .withColumn("machine_failure", F.col("machine_failure").cast(BooleanType()))
)

# ── 4. Filter out-of-range rows (log count before dropping) ───────────────────
valid = df.filter(
    F.col("air_temp").between(295.0, 310.0)
    & F.col("process_temp").between(305.0, 315.0)
    & F.col("rotational_speed").between(1100, 3000)
    & F.col("torque").between(3.0, 80.0)
    & F.col("tool_wear").between(0, 260)
    & F.col("product_type").isin("L", "M", "H")
    & F.col("udi").isNotNull()
)
dropped = df.count() - valid.count()
if dropped > 0:
    print(f"WARNING: {dropped} rows dropped (out-of-range sensor values)")

# ── 5. Write Parquet (snappy) ──────────────────────────────────────────────────
output_path = f"s3://{PROCESSED_BUCKET}/features/"
valid.coalesce(1).write.mode("overwrite").option("compression", "snappy").parquet(output_path)
print(f"Wrote {valid.count():,} rows → {output_path}")
