import pytest
import numpy as np
from ml.features import temp_diff, mechanical_power, wear_rate, overstrain_flag, build_feature_matrix


def test_temp_diff_positive():
    assert temp_diff(300.0, 310.0) == pytest.approx(10.0)


def test_temp_diff_zero():
    assert temp_diff(305.0, 305.0) == pytest.approx(0.0)


def test_mechanical_power_known_value():
    # P = 40 Nm × (1500 rpm × 2π / 60) = 40 × 157.08 ≈ 6283.2 W
    result = mechanical_power(40.0, 1500)
    assert result == pytest.approx(6283.18, rel=1e-3)


def test_mechanical_power_zero_torque():
    assert mechanical_power(0.0, 2000) == pytest.approx(0.0)


def test_wear_rate_value():
    # 150 min / 1500 rpm = 0.1
    assert wear_rate(150, 1500) == pytest.approx(0.1, rel=1e-6)


def test_wear_rate_zero_rpm_safe():
    # guard against division by zero — should return tool_wear / 1 = tool_wear
    assert wear_rate(100, 0) == pytest.approx(100.0)


def test_overstrain_flag_above_threshold():
    # 75.01 × 100 = 7501 > 7500
    assert overstrain_flag(75.01, 100) is True or overstrain_flag(75.01, 100) == True


def test_overstrain_flag_at_threshold():
    # 75.0 × 100 = 7500 — not greater than 7500
    assert overstrain_flag(75.0, 100) is False or overstrain_flag(75.0, 100) == False


def test_build_feature_matrix_shape():
    X = build_feature_matrix(298.0, 308.0, 1500, 40.0, 100)
    assert X.shape == (1, 10)


def test_build_feature_matrix_type_encoding_differs():
    X_L = build_feature_matrix(298.0, 308.0, 1500, 40.0, 100, "L")
    X_H = build_feature_matrix(298.0, 308.0, 1500, 40.0, 100, "H")
    assert X_L[0, 0] != X_H[0, 0]
