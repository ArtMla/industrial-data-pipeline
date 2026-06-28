"""Read Parquet features from S3 and bulk-insert into the PostgreSQL feature store."""
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from ml.features import mechanical_power, overstrain_flag, temp_diff, wear_rate

PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")
DATABASE_URL = os.getenv("DATABASE_URL", "")


def load_parquet() -> pd.DataFrame:
    path = f"s3://{PROCESSED_BUCKET}/features/"
    df = pd.read_parquet(path, storage_options={"anon": False})
    print(f"Loaded {len(df):,} rows from {path}")
    return df


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["temp_diff"] = temp_diff(df["air_temp"], df["process_temp"])
    df["mechanical_power"] = mechanical_power(df["torque"], df["rotational_speed"])
    df["wear_rate"] = wear_rate(df["tool_wear"], df["rotational_speed"])
    df["overstrain_flag"] = overstrain_flag(df["torque"], df["tool_wear"])
    return df


def bulk_insert(df: pd.DataFrame, conn) -> int:
    cols = [
        "udi", "product_id", "product_type",
        "air_temp", "process_temp", "rotational_speed", "torque", "tool_wear",
        "machine_failure", "temp_diff", "mechanical_power", "wear_rate", "overstrain_flag",
    ]
    records = [tuple(row[c] for c in cols) for _, row in df.iterrows()]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE features RESTART IDENTITY")
        execute_values(
            cur,
            f"INSERT INTO features ({', '.join(cols)}) VALUES %s",
            records,
            page_size=500,
        )
    conn.commit()
    return len(records)


def main() -> None:
    df = load_parquet()
    df = add_engineered_features(df)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        n = bulk_insert(df, conn)
        print(f"Inserted {n:,} rows → features table")
    finally:
        conn.close()

    print("\nNext: make train")


if __name__ == "__main__":
    main()
