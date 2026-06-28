"""
Physics-informed feature engineering for AI4I 2020 predictive maintenance data.

Pure functions: no I/O, no training-time state. Used identically in training
(ml/train.py) and API serving (api/router.py) — bugs here affect both.
"""
import numpy as np


def temp_diff(
    air_temp: float | np.ndarray,
    process_temp: float | np.ndarray,
) -> float | np.ndarray:
    """Process-to-air temperature delta (K). Elevated delta indicates thermal stress."""
    return process_temp - air_temp


def mechanical_power(
    torque: float | np.ndarray,
    rpm: float | np.ndarray,
) -> float | np.ndarray:
    """Mechanical power in Watts: P = τ × ω = torque × (rpm × 2π / 60)."""
    return torque * (rpm * 2 * np.pi / 60)


def wear_rate(
    tool_wear: float | np.ndarray,
    rpm: float | np.ndarray,
) -> float | np.ndarray:
    """Normalised tool degradation: wear minutes per unit rotational speed."""
    return tool_wear / np.maximum(rpm, 1)


def overstrain_flag(
    torque: float | np.ndarray,
    tool_wear: float | np.ndarray,
) -> bool | np.ndarray:
    """True when torque × tool_wear > 7500 — the OSF threshold from the dataset paper."""
    return (torque * tool_wear) > 7500


def build_feature_matrix(
    air_temp: float,
    process_temp: float,
    rotational_speed: int,
    torque: float,
    tool_wear: int,
    product_type: str = "M",
) -> np.ndarray:
    """Assemble a single-row feature matrix for API inference (matches training column order)."""
    type_enc = {"L": 0, "M": 1, "H": 2}.get(product_type, 1)
    return np.array([[
        type_enc,
        air_temp,
        process_temp,
        rotational_speed,
        torque,
        tool_wear,
        temp_diff(air_temp, process_temp),
        mechanical_power(torque, rotational_speed),
        wear_rate(tool_wear, rotational_speed),
        float(overstrain_flag(torque, tool_wear)),
    ]])
