"""Train and serialize the medical-condition classifier (Tech Challenge Fase 3).

CLI entrypoint (reusable — the Airflow DAG in Fase 6 will call this):

    python src/train.py \
        --data data/raw/medical_tc_train.csv \
        --test-data data/raw/medical_tc_test.csv \
        --model models/model.pkl \
        --classifier all \
        --test-size 0.2 \
        --random-state 42

Behaviour:
  1. load + preprocess text (lowercase, stopwords, cleaning);
  2. stratified train/test split with a fixed random_state;
  3. train RandomForest / LinearSVC / LogisticRegression, compare by macro-F1;
  4. serialize the best full pipeline (preprocess + TF-IDF + classifier);
  5. write metrics.json + classification_report.txt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import preprocess_texts  # noqa: E402

TEXT_COLUMN = "medical_abstract"
LABEL_COLUMN = "condition_label"

CONDITION_NAMES = [
    "neoplasms",
    "digestive system diseases",
    "nervous system diseases",
    "cardiovascular diseases",
    "general pathological conditions",
]

ALL_CLASSIFIERS = ["randomforest", "linearsvc", "logistic"]


def build_classifier(name: str, random_state: int):
    name = name.lower()
    if name in {"logistic", "logisticregression"}:
        return LogisticRegression(max_iter=2000, random_state=random_state)
    if name in {"linearsvc", "linear_svc", "svc", "svm"}:
        return LinearSVC(random_state=random_state, dual=False)
    if name in {"randomforest", "random_forest", "rf"}:
        return RandomForestClassifier(
            n_estimators=300, n_jobs=-1, random_state=random_state
        )
    raise ValueError(f"Unknown classifier: {name!r}")


def build_pipeline(classifier_name: str, random_state: int) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", FunctionTransformer(preprocess_texts, validate=False)),
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True
                ),
            ),
            ("clf", build_classifier(classifier_name, random_state)),
        ]
    )


# Hyperparameter grid for the linear models. RandomForest is kept at its
# defaults as a fast baseline (a full RF grid would be too slow to be useful).
LINEAR_GRID = {
    "clf__C": [0.1, 0.3, 1.0, 3.0, 10.0],
    "clf__class_weight": [None, "balanced"],
}


def candidates(random_state: int) -> dict:
    """Map classifier name -> (base pipeline, param grid or {})."""
    return {
        "randomforest": (build_pipeline("randomforest", random_state), {}),
        "linearsvc": (build_pipeline("linearsvc", random_state), LINEAR_GRID),
        "logistic": (build_pipeline("logistic", random_state), LINEAR_GRID),
    }


def compute_metrics(y_true, y_pred) -> dict:
    report = classification_report(
        y_true,
        y_pred,
        labels=range(1, 6),
        target_names=CONDITION_NAMES,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "per_class": {
            name: {k: report[name][k] for k in ("precision", "recall", "f1-score")}
            for name in CONDITION_NAMES
        },
    }


def report_text(y_true, y_pred) -> str:
    return classification_report(
        y_true,
        y_pred,
        labels=range(1, 6),
        target_names=CONDITION_NAMES,
        zero_division=0,
    )


def train_and_evaluate(df, classifier_name, test_size, random_state):
    df = df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    X = df[TEXT_COLUMN]
    y = df[LABEL_COLUMN].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )

    base_pipeline, param_grid = candidates(random_state)[classifier_name]
    if param_grid:
        search = GridSearchCV(
            base_pipeline,
            param_grid,
            cv=3,
            scoring="f1_macro",
            n_jobs=-1,
        )
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        best_params = search.best_params_
    else:
        base_pipeline.fit(X_train, y_train)
        pipeline = base_pipeline
        best_params = None

    y_pred = pipeline.predict(X_test)
    metrics = compute_metrics(y_test, y_pred)
    metrics["best_params"] = best_params
    metrics["train_size"] = int(len(X_train))
    metrics["test_size"] = int(len(X_test))
    return pipeline, metrics, y_test, y_pred


def evaluate_holdout(pipeline, csv_path):
    """Evaluate the trained pipeline on an external holdout CSV (official test split)."""
    df = pd.read_csv(csv_path).dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    y_true = df[LABEL_COLUMN].astype(int)
    y_pred = pipeline.predict(df[TEXT_COLUMN])
    return compute_metrics(y_true, y_pred)


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", required=True, help="Path to the training CSV.")
    p.add_argument(
        "--test-data",
        default=None,
        help="Optional held-out CSV (official test split).",
    )
    p.add_argument(
        "--model",
        default="models/model.pkl",
        help="Output path for the serialized pipeline.",
    )
    p.add_argument(
        "--metrics",
        default="models/metrics.json",
        help="Output path for metrics JSON.",
    )
    p.add_argument(
        "--report",
        default="models/classification_report.txt",
        help="Output path for the text report.",
    )
    p.add_argument(
        "--classifier",
        default="all",
        choices=ALL_CLASSIFIERS + ["all"],
        help="Classifier(s) to run; 'all' compares all three and keeps the best by macro-F1.",
    )
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--random-state", type=int, default=42)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    df = pd.read_csv(args.data)
    names = ALL_CLASSIFIERS if args.classifier == "all" else [args.classifier]

    results = {}
    for name in names:
        pipeline, metrics, y_test, y_pred = train_and_evaluate(
            df, name, args.test_size, args.random_state
        )
        results[name] = {
            "pipeline": pipeline,
            "metrics": metrics,
            "y_test": y_test,
            "y_pred": y_pred,
        }
        print(
            f"[{name:14s}] accuracy={metrics['accuracy']:.4f}  "
            f"macro_f1={metrics['macro_f1']:.4f}  "
            f"weighted_f1={metrics['weighted_f1']:.4f}"
        )

    best_name = max(
        results,
        key=lambda n: (
            results[n]["metrics"]["macro_f1"],
            results[n]["metrics"]["weighted_f1"],
        ),
    )
    best = results[best_name]
    print(f"\nBest classifier: {best_name} (macro_f1={best['metrics']['macro_f1']:.4f})")

    # Serialize the best full pipeline (preprocess + TF-IDF + classifier).
    model_path = Path(args.model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best["pipeline"], model_path)
    print(f"Serialized pipeline -> {model_path}")

    # Text report for the best model (reuse the stored predictions, no retrain).
    txt = report_text(best["y_test"], best["y_pred"])
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(txt, encoding="utf-8")

    # Assemble metrics JSON.
    payload = {
        "dataset": args.data,
        "best_classifier": best_name,
        "random_state": args.random_state,
        "test_size": args.test_size,
        "per_classifier": {n: r["metrics"] for n, r in results.items()},
    }
    if args.test_data:
        holdout_metrics = evaluate_holdout(best["pipeline"], args.test_data)
        payload["holdout_test"] = {"file": args.test_data, **holdout_metrics}
        print(
            f"[holdout] accuracy={holdout_metrics['accuracy']:.4f}  "
            f"macro_f1={holdout_metrics['macro_f1']:.4f}"
        )

    metrics_path = Path(args.metrics)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Metrics -> {metrics_path}")
    print(f"Report  -> {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
