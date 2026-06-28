import pandas as pd
import pandera as pa
import pytest
from etl.validate_schema import ai4i_schema


def valid_row() -> dict:
    return {
        "UDI": 1,
        "Product ID": "M14860",
        "Type": "M",
        "Air temperature [K]": 298.1,
        "Process temperature [K]": 308.6,
        "Rotational speed [rpm]": 1551,
        "Torque [Nm]": 42.8,
        "Tool wear [min]": 0,
        "Machine failure": 0,
    }


def test_valid_data_passes():
    df = pd.DataFrame([valid_row()])
    result = ai4i_schema.validate(df)
    assert len(result) == 1


def test_invalid_type_raises():
    row = valid_row()
    row["Type"] = "X"  # Not L/M/H
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaError):
        ai4i_schema.validate(df)


def test_air_temp_out_of_range_raises():
    row = valid_row()
    row["Air temperature [K]"] = 350.0  # Max allowed is 310
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaError):
        ai4i_schema.validate(df)


def test_rotational_speed_below_range_raises():
    row = valid_row()
    row["Rotational speed [rpm]"] = 500  # Min is 1100
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaError):
        ai4i_schema.validate(df)
