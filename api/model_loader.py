"""Singleton model loader — downloads XGBoost model from S3 once at startup."""
import os
import tempfile

import boto3
import numpy as np
import xgboost as xgb

PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")


class ModelLoader:
    _model: xgb.XGBClassifier | None = None
    _version: str = "unknown"

    @classmethod
    def load(cls, model_key: str | None = None) -> None:
        if model_key is None:
            model_key = os.getenv("MODEL_S3_KEY", "")
        if not model_key:
            raise RuntimeError("MODEL_S3_KEY env var not set — cannot load model from S3")

        s3 = boto3.client("s3")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            s3.download_fileobj(PROCESSED_BUCKET, model_key, f)
            tmp_path = f.name

        model = xgb.XGBClassifier()
        model.load_model(tmp_path)
        cls._model = model
        cls._version = model_key.split("/")[-1].replace(".json", "")
        print(f"Model loaded: {model_key}  (version={cls._version})")

    @classmethod
    def predict(cls, X: np.ndarray) -> tuple[float, dict[str, float]]:
        if cls._model is None:
            raise RuntimeError("Model not loaded — call ModelLoader.load() first")
        prob = float(cls._model.predict_proba(X)[0, 1])
        failure_modes = {
            "TWF": round(prob * 0.18, 4),
            "HDF": round(prob * 0.27, 4),
            "PWF": round(prob * 0.31, 4),
            "OSF": round(prob * 0.21, 4),
            "RNF": round(prob * 0.03, 4),
        }
        return prob, failure_modes

    @classmethod
    def get_version(cls) -> str:
        return cls._version
