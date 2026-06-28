import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

VALID_READING = {
    "air_temp": 298.1,
    "process_temp": 308.6,
    "rotational_speed": 1551,
    "torque": 42.8,
    "tool_wear": 0,
    "product_type": "M",
}


@pytest.mark.asyncio
async def test_health_returns_200(mock_db, mock_model):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "model_version" in r.json()


@pytest.mark.asyncio
async def test_predict_valid_returns_probability(mock_db, mock_model):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/predict", json=VALID_READING)
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["failure_probability"] <= 1.0
    assert isinstance(data["predicted_failure"], bool)
    assert "failure_modes" in data
    assert "prediction_id" in data


@pytest.mark.asyncio
async def test_predict_missing_field_returns_422(mock_db, mock_model):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/predict", json={"air_temp": 298.1})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_predict_out_of_range_returns_422(mock_db, mock_model):
    bad = {**VALID_READING, "air_temp": 400.0}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/predict", json=bad)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_metrics_has_required_keys(mock_db, mock_model, monkeypatch):
    monkeypatch.setattr("api.router._load_static_metrics", lambda: {
        "auc": 0.96, "precision": 0.91, "recall": 0.88, "f1": 0.89
    })
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/metrics")
    assert r.status_code == 200
    for key in ["auc", "precision", "recall", "f1", "total_predictions", "failure_rate_30d"]:
        assert key in r.json(), f"Missing key: {key}"
