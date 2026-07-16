"""Unit tests for ModelLoader's manifest-driven failure-mode wiring.

Captures the real (unpatched) classmethod at import time since conftest's
autouse mock_lifespan fixture stubs ModelLoader.load for every other test.
"""
import json
from unittest.mock import MagicMock

import numpy as np
import pytest

from api.model_loader import FAILURE_MODES, ModelLoader

_real_load = ModelLoader.load.__func__


class FakeModel:
    def __init__(self, key, positive_prob):
        self.key = key
        self.positive_prob = positive_prob

    def predict_proba(self, X):
        return np.array([[1 - self.positive_prob, self.positive_prob]])


def _fake_s3(manifest):
    s3 = MagicMock()
    if manifest is None:
        s3.get_object.side_effect = Exception("no manifest object")
    else:
        body = MagicMock()
        body.read.return_value = json.dumps(manifest).encode()
        s3.get_object.return_value = {"Body": body}
    return s3


MANIFEST = {
    "machine_failure": "models/xgb_20240101_120000.json",
    "twf": "models/xgb_twf_20240101_120000.json",
    "hdf": "models/xgb_hdf_20240101_120000.json",
    "pwf": "models/xgb_pwf_20240101_120000.json",
    "osf": "models/xgb_osf_20240101_120000.json",
    "rnf": "models/xgb_rnf_20240101_120000.json",
}


def test_load_wires_real_failure_mode_models_from_manifest(monkeypatch):
    s3 = _fake_s3(MANIFEST)
    monkeypatch.setattr("api.model_loader.boto3.client", lambda *a, **k: s3)
    monkeypatch.setattr(
        ModelLoader, "_download_model",
        staticmethod(lambda s3, key: FakeModel(key, positive_prob=0.7))
    )

    _real_load(ModelLoader, "models/xgb_20240101_120000.json")

    assert set(ModelLoader._failure_models) == set(FAILURE_MODES)
    for target in FAILURE_MODES:
        assert ModelLoader._failure_models[target].key == MANIFEST[target]

    prob, failure_modes = ModelLoader.predict(np.zeros((1, 10)))
    assert prob == pytest.approx(0.7)
    # each failure mode is served by its own model (0.7), not the fixed ratios
    for target in FAILURE_MODES:
        assert failure_modes[target.upper()] == pytest.approx(0.7)


def test_load_falls_back_to_fixed_ratios_when_manifest_missing(monkeypatch):
    s3 = _fake_s3(manifest=None)
    monkeypatch.setattr("api.model_loader.boto3.client", lambda *a, **k: s3)
    monkeypatch.setattr(
        ModelLoader, "_download_model",
        staticmethod(lambda s3, key: FakeModel(key, positive_prob=0.5))
    )

    _real_load(ModelLoader, "models/xgb_20240101_120000.json")

    assert ModelLoader._failure_models == {}
    prob, failure_modes = ModelLoader.predict(np.zeros((1, 10)))
    assert failure_modes["TWF"] == pytest.approx(round(prob * 0.18, 4))
    assert failure_modes["RNF"] == pytest.approx(round(prob * 0.03, 4))


def test_load_falls_back_per_target_when_manifest_partial(monkeypatch):
    partial = {**MANIFEST}
    del partial["osf"]
    s3 = _fake_s3(partial)
    monkeypatch.setattr("api.model_loader.boto3.client", lambda *a, **k: s3)
    monkeypatch.setattr(
        ModelLoader, "_download_model",
        staticmethod(lambda s3, key: FakeModel(key, positive_prob=0.4))
    )

    _real_load(ModelLoader, "models/xgb_20240101_120000.json")

    assert "osf" not in ModelLoader._failure_models
    prob, failure_modes = ModelLoader.predict(np.zeros((1, 10)))
    assert failure_modes["OSF"] == pytest.approx(round(prob * 0.21, 4))
    assert failure_modes["TWF"] == pytest.approx(0.4)
