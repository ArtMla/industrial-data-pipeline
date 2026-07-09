import os
import logging
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from xgboost import XGBClassifier
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models"

FEATURE_COLUMNS = [
    "type_encoded",
    "air_temp_k", "process_temp_k", "rotational_speed_rpm",
    "torque_nm", "tool_wear_min",
    "temp_delta_k", "power_w", "tool_wear_torque",
    "tool_wear_speed", "torque_speed_ratio",
]

# Primary target plus the five failure-mode flags, each trained as its own
# binary classifier — failure modes have distinct physical drivers (heat,
# power, overstrain, tool wear, random) so a shared multi-output model would
# blur signal that's specific to each mode.
TARGETS = ["machine_failure", "twf", "hdf", "pwf", "osf", "rnf"]


def load_data(engine) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM sensor_features", engine)
    log.info("Loaded %d rows from sensor_features", len(df))
    return df


def train_one(df: pd.DataFrame, target: str) -> dict:
    X = df[FEATURE_COLUMNS]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # Positive class is rare (failures are a small fraction of rows) — weight
    # it inversely to its frequency so the model doesn't just predict "no failure".
    n_pos = y_train.sum()
    n_neg = len(y_train) - n_pos
    scale_pos_weight = (n_neg / n_pos) if n_pos > 0 else 1.0

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "target": target,
        "n_positive": int(n_pos + y_test.sum()),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba) if y_test.nunique() > 1 else float("nan"),
    }
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    log.info(
        "[%s] precision=%.3f recall=%.3f f1=%.3f roc_auc=%.3f (tp=%d fp=%d fn=%d tn=%d)",
        target, metrics["precision"], metrics["recall"], metrics["f1"], metrics["roc_auc"],
        tp, fp, fn, tn,
    )

    return {"model": model, "metrics": metrics}


def main() -> None:
    db_url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', 5432)}/{os.environ['DB_NAME']}"
    )
    engine = create_engine(db_url)

    df = load_data(engine)

    MODEL_DIR.mkdir(exist_ok=True)

    results = []
    for target in TARGETS:
        result = train_one(df, target)
        results.append(result["metrics"])
        joblib.dump(result["model"], MODEL_DIR / f"xgb_{target}.joblib")

    report = pd.DataFrame(results).set_index("target")
    report.to_csv(MODEL_DIR / "metrics.csv")
    log.info("Training complete. Models and metrics.csv written to %s", MODEL_DIR)
    print(report.round(3).to_string())


if __name__ == "__main__":
    main()
