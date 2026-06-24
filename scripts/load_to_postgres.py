import os
import logging
import io

import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

S3_KEY = "raw/ai4i2020.csv"

EXPECTED_COLUMNS = {
    "UDI", "Product ID", "Type",
    "Air temperature [K]", "Process temperature [K]",
    "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
    "Machine failure", "TWF", "HDF", "PWF", "OSF", "RNF",
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    udi                     INTEGER PRIMARY KEY,
    product_id              VARCHAR(10)    NOT NULL,
    product_type            CHAR(1)        NOT NULL,
    air_temp_k              NUMERIC(6, 2)  NOT NULL,
    process_temp_k          NUMERIC(6, 2)  NOT NULL,
    rotational_speed_rpm    INTEGER        NOT NULL,
    torque_nm               NUMERIC(6, 2)  NOT NULL,
    tool_wear_min           INTEGER        NOT NULL,
    machine_failure         SMALLINT       NOT NULL,
    twf                     SMALLINT       NOT NULL,
    hdf                     SMALLINT       NOT NULL,
    pwf                     SMALLINT       NOT NULL,
    osf                     SMALLINT       NOT NULL,
    rnf                     SMALLINT       NOT NULL,
    loaded_at               TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
"""


def fetch_from_s3(bucket: str, key: str, region: str) -> pd.DataFrame:
    log.info("Fetching s3://%s/%s", bucket, key)
    s3 = boto3.client("s3", region_name=region)
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))
    log.info("Fetched %d rows, %d columns", len(df), len(df.columns))
    return df


def validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Null values found:\n{null_counts[null_counts > 0]}")

    invalid_types = df[~df["Type"].isin(["L", "M", "H"])]
    if not invalid_types.empty:
        raise ValueError(f"Unexpected product types: {df['Type'].unique()}")

    log.info("Validation passed — no nulls, columns and types OK")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "UDI": "udi",
        "Product ID": "product_id",
        "Type": "product_type",
        "Air temperature [K]": "air_temp_k",
        "Process temperature [K]": "process_temp_k",
        "Rotational speed [rpm]": "rotational_speed_rpm",
        "Torque [Nm]": "torque_nm",
        "Tool wear [min]": "tool_wear_min",
        "Machine failure": "machine_failure",
        "TWF": "twf",
        "HDF": "hdf",
        "PWF": "pwf",
        "OSF": "osf",
        "RNF": "rnf",
    })


def load(df: pd.DataFrame, engine) -> None:
    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()

    df.to_sql(
        "sensor_readings",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=500,
    )
    log.info("Loaded %d rows into sensor_readings", len(df))


def main() -> None:
    bucket = os.environ["S3_BUCKET_NAME"]
    region = os.environ.get("AWS_REGION", "eu-north-1")
    db_url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', 5432)}/{os.environ['DB_NAME']}"
    )

    df = fetch_from_s3(bucket, S3_KEY, region)
    df = validate(df)
    df = transform(df)

    engine = create_engine(db_url)
    load(df, engine)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
