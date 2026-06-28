"""Local pandera schema validation for the AI4I 2020 CSV. Run before uploading to S3."""
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema

ai4i_schema = DataFrameSchema(
    {
        "UDI": Column(int, Check.greater_than(0)),
        "Product ID": Column(str),
        "Type": Column(str, Check.isin(["L", "M", "H"])),
        "Air temperature [K]": Column(float, Check.in_range(295.0, 310.0)),
        "Process temperature [K]": Column(float, Check.in_range(305.0, 315.0)),
        "Rotational speed [rpm]": Column(int, Check.in_range(1100, 3000)),
        "Torque [Nm]": Column(float, Check.in_range(3.0, 80.0)),
        "Tool wear [min]": Column(int, Check.in_range(0, 260)),
        "Machine failure": Column(int, Check.isin([0, 1])),
    },
    coerce=True,
)


def validate(path: str | Path = "data/raw/ai4i2020.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    validated = ai4i_schema.validate(df)
    print(f"Schema OK — {len(validated):,} rows validated")
    return validated


if __name__ == "__main__":
    validate()
