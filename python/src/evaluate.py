"""Held-out evaluation, confidence diagnostics and reproducible reports."""

import argparse
import json
import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
)

from src.model import load_model, refit_pipeline
from src.utils import (
    ROOT,
    file_hash,
    load_config,
    project_path,
    save_csv,
    save_json,
)

LOGGER = logging.getLogger(__name__)


def evaluate_model(model, test, output_dir=None, figure_dir=None):
    """Evaluate held-out tickets and optionally export reports."""
    labels = list(model.classes_)
    actual = test["clasificacion"].to_numpy()
    predicted = model.predict(test["texto"])
    probabilities = model.predict_proba(test["texto"])
    confidence = probabilities.max(axis=1)
    one_hot = (actual[:, None] == np.array(labels)).astype(float)
    report = classification_report(
        actual,
        predicted,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(actual, predicted)),
        "f1_macro": float(f1_score(actual, predicted, average="macro")),
        "f1_weighted": float(f1_score(actual, predicted, average="weighted")),
        "log_loss": float(log_loss(actual, probabilities, labels=labels)),
        "brier_multiclass": float(
            np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))
        ),
        "n_test": len(test),
        "classes": labels,
        "classification_report": report,
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=labels
        ).tolist(),
    }
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = save_csv(
            pd.DataFrame(report).T, output_dir / "classification_report.csv"
        )
        rows = pd.DataFrame(
            {
                "row_id": test.index,
                "real": actual,
                "predicha": predicted,
                "confianza": confidence,
                "correcta": actual == predicted,
            }
        )
        predictions_path = save_csv(
            rows, output_dir / "test_predictions.csv", index=False
        )
        errors_path = save_csv(
            rows.loc[~rows["correcta"]], output_dir / "errors.csv", index=False
        )
        metrics["artifact_files"] = {
            "classification_report": report_path.name,
            "test_predictions": predictions_path.name,
            "errors": errors_path.name,
        }
        save_json(output_dir / "test_metrics.json", metrics)
    if figure_dir:
        figure_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            metrics["confusion_matrix"],
            annot=True,
            fmt="d",
            xticklabels=labels,
            yticklabels=labels,
            cmap="Blues",
            ax=ax,
        )
        ax.set(
            xlabel="Predicción",
            ylabel="Clase real",
            title="Matriz de confusión (test)",
        )
        fig.tight_layout()
        fig.savefig(figure_dir / "confusion_matrix.png", dpi=160)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(7, 5))
        observed, expected = calibration_curve(
            (actual == predicted).astype(int),
            confidence,
            n_bins=5,
            strategy="uniform",
        )
        ax.plot(expected, observed, "o-", label="Confianza máxima")
        ax.plot([0, 1], [0, 1], "--", color="gray", label="Referencia ideal")
        ax.set(
            xlabel="Confianza media",
            ylabel="Fracción correcta",
            title=f"Fiabilidad de confianza ({len(test)} tickets)",
            xlim=(0, 1),
            ylim=(0, 1),
        )
        ax.legend()
        fig.tight_layout()
        fig.savefig(figure_dir / "confidence_reliability.png", dpi=160)
        plt.close(fig)
    return metrics


def main():
    """Re-evaluate the saved model only against its recorded test partition."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    try:
        config = load_config(args.config)
        model_path = project_path(config["model_path"])
        metadata = json.loads(
            (ROOT / "results/metrics/training_summary.json").read_text(
                encoding="utf-8"
            )
        )
        if file_hash(model_path) != metadata["model_sha256"]:
            raise ValueError(
                "El modelo no coincide con la evaluación registrada."
            )
        recorded_path = metadata.get("evaluation_model_path")
        evaluation_path = (
            project_path(recorded_path) if recorded_path else None
        )
        if evaluation_path is not None:
            expected_hash = metadata.get(
                "evaluation_model_sha256", metadata["model_sha256"]
            )
            if file_hash(evaluation_path) != expected_hash:
                raise ValueError("El modelo de evaluación fue modificado.")
            evaluation_model = load_model(evaluation_path)
        else:
            train_path = ROOT / "data/processed/evaluation_train.csv"
            expected_hash = metadata.get("evaluation_train_sha256")
            if not expected_hash or file_hash(train_path) != expected_hash:
                raise ValueError("La partición de evaluación fue modificada.")
            evaluation_train = pd.read_csv(
                train_path, index_col="row_id", keep_default_na=False
            )
            evaluation_model = refit_pipeline(
                load_model(model_path),
                evaluation_train.texto,
                evaluation_train.clasificacion,
            )
        test_path = ROOT / "data/processed/test.csv"
        if file_hash(test_path) != metadata["test_sha256"]:
            raise ValueError(
                "El test cambió desde el entrenamiento; no es comparable."
            )
        test = pd.read_csv(
            test_path, index_col="row_id", keep_default_na=False
        )
        metrics = evaluate_model(
            evaluation_model,
            test,
            ROOT / "results/metrics",
            ROOT / "documentacion/imagenes",
        )
        fit_all = metadata.get("fit_policy") == "full_corpus_refit"
        metrics["evaluation_model_path"] = (
            str(evaluation_path.relative_to(ROOT)) if evaluation_path else None
        )
        metrics["evaluation_reconstructed_in_memory"] = evaluation_path is None
        metrics["evaluation_training_rows"] = metadata.get(
            "n_evaluation_train", metadata["n_train"]
        )
        metrics["final_model_training_rows"] = metadata["n_train"]
        metrics["applies_to_final_model"] = not fit_all
        save_json(ROOT / "results/metrics/test_metrics.json", metrics)
        LOGGER.info(
            "Evaluando el modelo de %d correos: %s",
            metrics["evaluation_training_rows"],
            evaluation_path
            or "reconstruido en memoria, sin guardar otro .pkl",
        )
        if fit_all:
            LOGGER.info(
                "El modelo final de %d correos requiere datos nuevos "
                "para una evaluación independiente.",
                metadata["n_train"],
            )
        LOGGER.info(
            "Accuracy %.3f; F1 macro %.3f",
            metrics["accuracy"],
            metrics["f1_macro"],
        )
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error de evaluación: {exc}\n")


if __name__ == "__main__":
    main()
