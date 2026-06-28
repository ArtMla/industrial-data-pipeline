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

PARAMS: dict = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "eval_metric": "logloss",
    # AI4I 2020 has 3.4% failure rate → ~28:1 imbalance
    "scale_pos_weight": 28,
}

FEATURE_COLS = [
    "product_type_enc", "air_temp", "process_temp", "rotational_speed",
    "torque", "tool_wear", "temp_diff", "mechanical_power", "wear_rate", "overstrain_flag",
]


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


def push_to_s3(model: xgb.XGBClassifier, metrics: dict, version: str) -> str:
    s3 = boto3.client("s3")
    model_key = f"models/xgb_{version}.json"
    metrics_key = f"models/xgb_{version}_metrics.json"

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        model.save_model(f.name)
        s3.upload_file(f.name, PROCESSED_BUCKET, model_key)

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=metrics_key,
        Body=json.dumps({**metrics, "version": version}).encode(),
    )

    with open(".model_version", "w") as f:
        f.write(model_key)

    print(f"Model → s3://{PROCESSED_BUCKET}/{model_key}")
    return model_key


def main() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("pred-maint-xgboost")

    df = load_features()
    X = build_X(df)
    y = df["machine_failure"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"Train: {len(X_train):,}  Test: {len(X_test):,}  Failures in test: {y_test.sum()}")

    with mlflow.start_run():
        mlflow.log_params(PARAMS)

        model = xgb.XGBClassifier(**PARAMS)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

        metrics = evaluate(model, X_test, y_test)
        mlflow.log_metrics(metrics)

        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_key = push_to_s3(model, metrics, version)
        mlflow.log_param("model_s3_key", model_key)

    print(f"\nDone — AUC: {metrics['auc']:.4f}  F1: {metrics['f1']:.4f}")
    print(f"MODEL_S3_KEY={model_key}")
    print("\nNext: make api  (or update MODEL_S3_KEY in .env and restart the API container)")


if __name__ == "__main__":
    main()
