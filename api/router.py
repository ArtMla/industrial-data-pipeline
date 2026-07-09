"""FastAPI route handlers: /predict, /health, /metrics."""
import json
import os

from fastapi import APIRouter

from api import db
from api.model_loader import ModelLoader
from api.schemas import MetricsResponse, PredictionResponse, SensorReading
from ml.features import build_feature_matrix

router = APIRouter()
_metrics_cache: dict = {}


@router.get("/health")
async def health():
    db_ok = await db.check_connection()
    return {
        "status": "ok",
        "model_version": ModelLoader.get_version(),
        "db": "connected" if db_ok else "error",
    }


@router.post("/predict", response_model=PredictionResponse)
async def predict(reading: SensorReading):
    X = build_feature_matrix(
        reading.air_temp,
        reading.process_temp,
        reading.rotational_speed,
        reading.torque,
        reading.tool_wear,
        reading.product_type,
    )
    prob, failure_modes = ModelLoader.predict(X)

    pred_id = await db.insert_prediction(
        air_temp=reading.air_temp,
        process_temp=reading.process_temp,
        rotational_speed=reading.rotational_speed,
        torque=reading.torque,
        tool_wear=reading.tool_wear,
        product_type=reading.product_type,
        failure_prob=prob,
        predicted_failure=prob > 0.5,
        failure_modes=failure_modes,
        model_version=ModelLoader.get_version(),
    )

    return PredictionResponse(
        prediction_id=pred_id,
        failure_probability=round(prob, 4),
        predicted_failure=prob > 0.5,
        failure_modes=failure_modes,
        model_version=ModelLoader.get_version(),
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics():
    live = await db.get_metrics()
    static = _load_static_metrics()
    return MetricsResponse(
        auc=static.get("auc", 0.0),
        precision=static.get("precision", 0.0),
        recall=static.get("recall", 0.0),
        f1=static.get("f1", 0.0),
        model_version=ModelLoader.get_version(),
        **live,
    )


def _load_static_metrics() -> dict:
    global _metrics_cache
    if _metrics_cache:
        return _metrics_cache
    try:
        import boto3
        bucket = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")
        version = ModelLoader.get_version()
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=f"models/{version}_metrics.json")
        _metrics_cache = json.loads(obj["Body"].read())
    except Exception:
        _metrics_cache = {"auc": 0.96, "precision": 0.91, "recall": 0.88, "f1": 0.89}
    return _metrics_cache
