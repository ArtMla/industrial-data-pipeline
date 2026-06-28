"""Model evaluation utilities — classification report, AUC-ROC, confusion matrix."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate(model: xgb.XGBClassifier, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print("\n── Classification Report ──────────────────────────────────")
    print(classification_report(y_test, y_pred, target_names=["no failure", "failure"]))
    print(f"AUC-ROC: {auc:.4f}")

    _save_confusion_matrix(confusion_matrix(y_test, y_pred))

    return {
        "auc": round(auc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_test": int(len(y_test)),
    }


def _save_confusion_matrix(cm: np.ndarray, path: str = "docs/confusion_matrix.png") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["No Failure", "Failure"])
    ax.set_yticklabels(["No Failure", "Failure"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    threshold = cm.max() / 2
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > threshold else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Confusion matrix → {path}")
