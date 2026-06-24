import os
import logging
import math

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sensor_features (
    udi                     INTEGER PRIMARY KEY,
    product_type            CHAR(1)        NOT NULL,
    type_encoded            SMALLINT       NOT NULL,

    -- Raw sensor readings
    air_temp_k              NUMERIC(6, 2)  NOT NULL,
    process_temp_k          NUMERIC(6, 2)  NOT NULL,
    rotational_speed_rpm    INTEGER        NOT NULL,
    torque_nm               NUMERIC(6, 2)  NOT NULL,
    tool_wear_min           INTEGER        NOT NULL,

    -- Engineered features
    temp_delta_k            NUMERIC(6, 2)  NOT NULL,
    power_w                 NUMERIC(10, 2) NOT NULL,
    tool_wear_torque        NUMERIC(10, 2) NOT NULL,
    tool_wear_speed         NUMERIC(10, 2) NOT NULL,
    torque_speed_ratio      NUMERIC(10, 4) NOT NULL,

    -- Targets
    machine_failure         SMALLINT       NOT NULL,
    twf                     SMALLINT       NOT NULL,
    hdf                     SMALLINT       NOT NULL,
    pwf                     SMALLINT       NOT NULL,
    osf                     SMALLINT       NOT NULL,
    rnf                     SMALLINT       NOT NULL,

    created_at              TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
"""

TYPE_ENCODING = {"L": 0, "M": 1, "H": 2}


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Ordinal encode product quality tier (L < M < H reflects increasing precision)
    out["type_encoded"] = out["product_type"].map(TYPE_ENCODING)

    # Temperature differential: gap between process and ambient heat
    # A collapsing differential often precedes heat-related failures (HDF)
    out["temp_delta_k"] = out["process_temp_k"] - out["air_temp_k"]

    # Mechanical power (Watts): P = τ × ω, where ω = rpm × 2π/60
    out["power_w"] = out["torque_nm"] * (out["rotational_speed_rpm"] * 2 * math.pi / 60)

    # Wear–torque interaction: worn tools demand more torque — compound stress indicator
    out["tool_wear_torque"] = out["tool_wear_min"] * out["torque_nm"]

    # Wear–speed interaction: high speed on a worn tool accelerates failure (TWF, OSF)
    out["tool_wear_speed"] = out["tool_wear_min"] * out["rotational_speed_rpm"]

    # Torque-to-speed ratio: proxy for cutting load; spikes signal overload (PWF)
    out["torque_speed_ratio"] = out["torque_nm"] / out["rotational_speed_rpm"]

    log.info("Engineered 5 features for %d rows", len(out))
    return out


def load(df: pd.DataFrame, engine) -> None:
    cols = [
        "udi", "product_type", "type_encoded",
        "air_temp_k", "process_temp_k", "rotational_speed_rpm",
        "torque_nm", "tool_wear_min",
        "temp_delta_k", "power_w", "tool_wear_torque",
        "tool_wear_speed", "torque_speed_ratio",
        "machine_failure", "twf", "hdf", "pwf", "osf", "rnf",
    ]

    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()

    df[cols].to_sql(
        "sensor_features",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=500,
    )
    log.info("Loaded %d rows into sensor_features", len(df))


def main() -> None:
    db_url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', 5432)}/{os.environ['DB_NAME']}"
    )
    engine = create_engine(db_url)

    log.info("Reading sensor_readings from PostgreSQL")
    df = pd.read_sql("SELECT * FROM sensor_readings", engine)
    log.info("Loaded %d rows", len(df))

    df = engineer(df)
    load(df, engine)
    log.info("Feature engineering complete.")


if __name__ == "__main__":
    main()
