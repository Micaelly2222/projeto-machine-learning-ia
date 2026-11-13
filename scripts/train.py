import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, cross_validate

from app.classifier import DocumentClassifier, build_pipeline
from app.config import ROOT_DIR, settings
from scripts.generate_dataset import generate

REPORTS_DIR = ROOT_DIR / "reports"


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(generate(per_class=150, seed=42)).to_csv(path, index=False, encoding="utf-8")
    return pd.read_csv(path, encoding="utf-8")


def holdout_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    held_out = df.groupby("label")["template"].agg(lambda t: sorted(t.unique())[-1])
    mask = df["template"].isin(held_out.values)
    return df[~mask], df[mask]


def write_markdown(metrics: dict, labels: list[str], matrix: list[list[int]], path: Path) -> None:
    lines = [
        "# Document classifier report",
        "",
        f"Trained at {metrics['trained_at']} on {metrics['n_documents']} documents, {len(labels)} classes.",
        "",
        "## Held-out templates",
        "",
        "The test set uses one template per class that the model never saw during training.",
        "",
        f"- Accuracy: **{metrics['holdout']['accuracy']:.3f}**",
        f"- Macro F1: **{metrics['holdout']['macro_f1']:.3f}**",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    report = metrics["holdout"]["per_class"]
    for label in labels:
        r = report[label]
        lines.append(f"| {label} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} | {int(r['support'])} |")
    lines += [
        "",
        "## 5-fold cross-validation (grouped by template)",
        "",
        f"- Accuracy: **{metrics['cross_validation']['accuracy_mean']:.3f}** ± {metrics['cross_validation']['accuracy_std']:.3f}",
        f"- Macro F1: **{metrics['cross_validation']['macro_f1_mean']:.3f}** ± {metrics['cross_validation']['macro_f1_std']:.3f}",
        "",
        "## Confusion matrix (held-out templates)",
        "",
        "Rows are true classes, columns are predicted classes.",
        "",
        "| | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
    ]
    for label, row in zip(labels, matrix):
        lines.append(f"| **{label}** | " + " | ".join(str(v) for v in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def train_and_save(dataset_path: Path | None = None, model_path: Path | None = None) -> dict:
    dataset_path = dataset_path or settings.dataset_path
    model_path = model_path or settings.model_path
    df = load_dataset(dataset_path)
    labels = sorted(df["label"].unique())

    train_df, test_df = holdout_split(df)
    pipeline = build_pipeline().fit(train_df["text"], train_df["label"])
    predicted = pipeline.predict(test_df["text"])

    cv = cross_validate(
        build_pipeline(),
        df["text"],
        df["label"],
        groups=df["template"],
        cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42),
        scoring={"accuracy": "accuracy", "macro_f1": "f1_macro"},
    )

    final = build_pipeline().fit(df["text"], df["label"])
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    metrics = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "n_documents": int(len(df)),
        "classes": labels,
        "holdout": {
            "n_documents": int(len(test_df)),
            "accuracy": float(accuracy_score(test_df["label"], predicted)),
            "macro_f1": float(f1_score(test_df["label"], predicted, average="macro")),
            "per_class": classification_report(test_df["label"], predicted, output_dict=True, zero_division=0),
        },
        "cross_validation": {
            "folds": 5,
            "accuracy_mean": float(cv["test_accuracy"].mean()),
            "accuracy_std": float(cv["test_accuracy"].std()),
            "macro_f1_mean": float(cv["test_macro_f1"].mean()),
            "macro_f1_std": float(cv["test_macro_f1"].std()),
        },
    }

    DocumentClassifier(final, metrics).save(model_path)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    matrix = confusion_matrix(test_df["label"], predicted, labels=labels).tolist()
    write_markdown(metrics, labels, matrix, REPORTS_DIR / "classifier_report.md")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=None)
    args = parser.parse_args()
    metrics = train_and_save(args.dataset, args.model)
    print(f"Held-out accuracy: {metrics['holdout']['accuracy']:.3f}  macro F1: {metrics['holdout']['macro_f1']:.3f}")
    print(f"CV accuracy: {metrics['cross_validation']['accuracy_mean']:.3f} ± {metrics['cross_validation']['accuracy_std']:.3f}")


if __name__ == "__main__":
    main()
