"""CLI batch inference — loads model from S3 and scores a single sensor reading."""
import argparse
import json
import os
import tempfile

import boto3
import xgboost as xgb

from ml.features import build_feature_matrix

PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")


def load_model(model_key: str) -> xgb.XGBClassifier:
    s3 = boto3.client("s3")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        s3.download_fileobj(PROCESSED_BUCKET, model_key, f)
        tmp = f.name
    m = xgb.XGBClassifier()
    m.load_model(tmp)
    return m


def resolve_model_key(arg: str | None) -> str:
    if arg:
        return arg
    if os.path.exists(".model_version"):
        return open(".model_version").read().strip()
    raise SystemExit("ERROR: provide --model-key or run `make train` first")


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict machine failure from sensor reading")
    parser.add_argument("--model-key", default=None)
    parser.add_argument("--air-temp", type=float, default=300.0)
    parser.add_argument("--process-temp", type=float, default=310.0)
    parser.add_argument("--rpm", type=int, default=1500)
    parser.add_argument("--torque", type=float, default=40.0)
    parser.add_argument("--tool-wear", type=int, default=100)
    parser.add_argument("--product-type", default="M", choices=["L", "M", "H"])
    args = parser.parse_args()

    model_key = resolve_model_key(args.model_key)
    model = load_model(model_key)

    X = build_feature_matrix(
        args.air_temp, args.process_temp, args.rpm,
        args.torque, args.tool_wear, args.product_type,
    )
    prob = float(model.predict_proba(X)[0, 1])
    print(json.dumps({
        "failure_probability": round(prob, 4),
        "predicted_failure": prob > 0.5,
        "model_key": model_key,
    }, indent=2))


if __name__ == "__main__":
    main()
