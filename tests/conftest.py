"""Shared test fixtures — mocks DB and model to avoid live AWS/PostgreSQL in CI."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_lifespan(monkeypatch):
    """Prevent lifespan from calling real DB init and S3 model download."""
    async def noop_init(): pass
    async def noop_close(): pass

    monkeypatch.setattr("api.db.init_pool", noop_init)
    monkeypatch.setattr("api.db.close_pool", noop_close)
    monkeypatch.setattr("api.model_loader.ModelLoader.load", classmethod(lambda cls, k=None: None))
    monkeypatch.setattr("api.model_loader.ModelLoader._version", "test_v1")


@pytest.fixture
def mock_db(monkeypatch):
    monkeypatch.setattr("api.db.insert_prediction", AsyncMock(return_value=1))
    monkeypatch.setattr("api.db.get_metrics", AsyncMock(return_value={
        "total_predictions": 42,
        "failure_rate_30d": 0.034,
    }))
    monkeypatch.setattr("api.db.check_connection", AsyncMock(return_value=True))


@pytest.fixture
def mock_model(monkeypatch):
    from api.model_loader import ModelLoader
    monkeypatch.setattr(
        ModelLoader, "predict",
        staticmethod(lambda X: (0.12, {"TWF": 0.02, "HDF": 0.03, "PWF": 0.04, "OSF": 0.02, "RNF": 0.00}))
    )
    monkeypatch.setattr(ModelLoader, "get_version", staticmethod(lambda: "test_v1"))
