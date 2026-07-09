"""XGBoost training pipeline with MLflow tracking and S3 model artifact push."""
import json
import os
import tempfile
from datetime import datetime

import boto3
import mlflow
import numpy as np
import pandas as pd
import psycopg2
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from ml.evaluate import evaluate

DATABASE_URL = os.getenv("DATABASE_URL", "")
PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")

BASE_PARAMS: dict = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "eval_metric": "logloss",
}

FEATURE_COLS = [
    "product_type_enc", "air_temp", "process_temp", "rotational_speed",
    "torque", "tool_wear", "temp_diff", "mechanical_power", "wear_rate", "overstrain_flag",
]

# machine_failure is the primary target; the five failure modes each have a
# distinct physical driver (heat, power, overstrain, tool wear, random) so
# they're trained as separate binary classifiers rather than one multi-label model.
FAILURE_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]
TARGETS = ["machine_failure"] + FAILURE_MODES


def load_features() -> pd.DataFrame:
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM features ORDER BY id", conn)
    conn.close()
    print(f"Loaded {len(df):,} rows from feature store")
    return df


def build_X(df: pd.DataFrame) -> np.ndarray:
    df = df.copy()
    le = LabelEncoder()
    df["product_type_enc"] = le.fit_transform(df["product_type"])
    return df[FEATURE_COLS].values


def push_to_s3(model: xgb.XGBClassifier, metrics: dict, version: str, target: str) -> str:
    s3 = boto3.client("s3")
    # machine_failure keeps the unsuffixed key so it stays compatible with
    # api/model_loader.py's MODEL_S3_KEY, which points at a single primary model.
    stem = "xgb" if target == "machine_failure" else f"xgb_{target}"
    model_key = f"models/{stem}_{version}.json"
    metrics_key = f"models/{stem}_{version}_metrics.json"

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        model.save_model(f.name)
        s3.upload_file(f.name, PROCESSED_BUCKET, model_key)

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=metrics_key,
        Body=json.dumps({**metrics, "version": version, "target": target}).encode(),
    )

    print(f"Model [{target}] → s3://{PROCESSED_BUCKET}/{model_key}")
    return model_key


def train_target(
    X_train: np.ndarray, X_test: np.ndarray,
    y_train: np.ndarray, y_test: np.ndarray,
    target: str,
) -> tuple[xgb.XGBClassifier, dict]:
    n_pos = int(y_train.sum())
    # Each target has its own positive-class rate (failure modes are rarer than
    # machine_failure overall), so scale_pos_weight is computed per target rather
    # than hardcoded for the 3.4%/~28:1 machine_failure ratio.
    scale_pos_weight = (len(y_train) - n_pos) / n_pos if n_pos > 0 else 1.0
    params = {**BASE_PARAMS, "scale_pos_weight": scale_pos_weight}

    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    metrics = evaluate(model, X_test, y_test, target=target)
    mlflow.log_params({f"{k}": v for k, v in params.items()})
    mlflow.log_metrics({k: v for k, v in metrics.items() if v == v})  # drop NaN
    return model, metrics


def main() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("pred-maint-xgboost")

    df = load_features()
    X = build_X(df)
    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    manifest: dict[str, str] = {}
    primary_metrics: dict = {}

    for target in TARGETS:
        y = df[target].astype(int).values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        print(f"\n[{target}] Train: {len(X_train):,}  Test: {len(X_test):,}  Positives in test: {y_test.sum()}")

        with mlflow.start_run(run_name=target):
            mlflow.set_tag("target", target)
            model, metrics = train_target(X_train, X_test, y_train, y_test, target)
            model_key = push_to_s3(model, metrics, version, target)
            mlflow.log_param("model_s3_key", model_key)

        manifest[target] = model_key
        if target == "machine_failure":
            primary_metrics = metrics

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=f"models/manifest_{version}.json",
        Body=json.dumps(manifest, indent=2).encode(),
    )
    with open(".model_version", "w") as f:
        f.write(manifest["machine_failure"])

    print(f"\nDone — machine_failure AUC: {primary_metrics['auc']:.4f}  F1: {primary_metrics['f1']:.4f}")
    print(f"MODEL_S3_KEY={manifest['machine_failure']}")
    print(f"Manifest (all 6 targets) → s3://{PROCESSED_BUCKET}/models/manifest_{version}.json")
    print("\nNext: make api  (or update MODEL_S3_KEY in .env and restart the API container)")
    print("Note: api/model_loader.py currently only serves the primary machine_failure model —")
    print("the 5 failure-mode models are trained and stored but not yet wired into /predict.")


if __name__ == "__main__":
    main()
