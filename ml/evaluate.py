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


def evaluate(
    model: xgb.XGBClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    target: str = "machine_failure",
) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # A target with zero positives in the test split (rare failure modes on a small
    # split) makes roc_auc_score undefined — report NaN rather than raising.
    auc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else float("nan")
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"\n── Classification Report: {target} ──────────────────────────")
    print(classification_report(y_test, y_pred, target_names=[f"no {target}", target], zero_division=0))
    print(f"AUC-ROC: {auc:.4f}")

    _save_confusion_matrix(confusion_matrix(y_test, y_pred), target)

    return {
        "auc": round(auc, 4) if auc == auc else auc,  # keep NaN as NaN, round otherwise
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_test": int(len(y_test)),
    }


def _save_confusion_matrix(cm: np.ndarray, target: str) -> None:
    path = f"docs/confusion_matrix_{target}.png"
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
