"""Singleton model loader — downloads XGBoost models from S3 once at startup."""
import json
import os
import tempfile

import boto3
import numpy as np
import xgboost as xgb

PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")

# Must match ml/train.py's FAILURE_MODES — the 5 per-mode classifiers trained
# alongside the primary machine_failure model.
FAILURE_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]

# Historical failure-mode ratios from the AI4I 2020 dataset, used only as a
# fallback when a target's model isn't in the manifest (e.g. MODEL_S3_KEY
# points at a version trained before per-mode models existed).
_FALLBACK_RATIOS = {"twf": 0.18, "hdf": 0.27, "pwf": 0.31, "osf": 0.21, "rnf": 0.03}


class ModelLoader:
    _model: xgb.XGBClassifier | None = None
    _failure_models: dict[str, xgb.XGBClassifier] = {}
    _version: str = "unknown"

    @classmethod
    def load(cls, model_key: str | None = None) -> None:
        if model_key is None:
            model_key = os.getenv("MODEL_S3_KEY", "")
        if not model_key:
            raise RuntimeError("MODEL_S3_KEY env var not set — cannot load model from S3")

        s3 = boto3.client("s3")
        cls._model = cls._download_model(s3, model_key)
        cls._version = model_key.split("/")[-1].replace(".json", "")
        print(f"Model loaded: {model_key}  (version={cls._version})")

        cls._failure_models = {}
        version_stamp = cls._version.removeprefix("xgb_")
        manifest_key = f"models/manifest_{version_stamp}.json"
        try:
            obj = s3.get_object(Bucket=PROCESSED_BUCKET, Key=manifest_key)
            manifest = json.loads(obj["Body"].read())
        except Exception as e:
            print(f"Warning: could not load {manifest_key} ({e}) — "
                  f"falling back to fixed failure-mode ratios")
            manifest = {}

        for target in FAILURE_MODES:
            key = manifest.get(target)
            if not key:
                continue
            try:
                cls._failure_models[target] = cls._download_model(s3, key)
            except Exception as e:
                print(f"Warning: could not load '{target}' model from {key} ({e})")

    @staticmethod
    def _download_model(s3, model_key: str) -> xgb.XGBClassifier:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            s3.download_fileobj(PROCESSED_BUCKET, model_key, f)
            tmp_path = f.name
        model = xgb.XGBClassifier()
        model.load_model(tmp_path)
        return model

    @classmethod
    def predict(cls, X: np.ndarray) -> tuple[float, dict[str, float]]:
        if cls._model is None:
            raise RuntimeError("Model not loaded — call ModelLoader.load() first")
        prob = float(cls._model.predict_proba(X)[0, 1])
        failure_modes = {
            target.upper(): (
                round(float(cls._failure_models[target].predict_proba(X)[0, 1]), 4)
                if target in cls._failure_models
                else round(prob * _FALLBACK_RATIOS[target], 4)
            )
            for target in FAILURE_MODES
        }
        return prob, failure_modes

    @classmethod
    def get_version(cls) -> str:
        return cls._version
