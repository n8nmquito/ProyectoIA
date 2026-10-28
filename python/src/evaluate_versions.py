"""Verify saved datasets and compare the four classifier versions."""

import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate

from src.data_processing import load_data
from src.evaluate_new import evaluate_new, training_subset_for_model
from src.model import build_pipeline, load_model
from src.utils import ROOT, file_hash, load_config, save_csv, save_json

SIZES = (10, 100, 200, 300)
LOGGER = logging.getLogger(__name__)


def verify_artifact(size, corpus):
    """Check the fitted manifest and exact exported records for a version."""
    model_path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
    dataset_path = ROOT / "data/train" / f"correos_{size}.json"
    pipeline = load_model(model_path)
    subset = training_subset_for_model(pipeline, corpus)
    exported = load_data(dataset_path)
    columns = ["titulo", "cuerpo", "clasificacion"]
    if len(subset) != size or len(exported) != size:
        raise ValueError(f"Cantidad incorrecta para el modelo de {size}.")
    if subset[columns].to_dict("records") != exported[columns].to_dict(
        "records"
    ):
        raise ValueError(f"El dataset no corresponde al modelo de {size}.")
    return pipeline, subset, model_path, dataset_path


def cross_validation(pipeline, frame, folds, seed):
    """Measure fresh clones only when calibration is valid in every fold."""
    folds = min(folds, int(frame.clasificacion.value_counts().min()))
    splitter = StratifiedKFold(folds, shuffle=True, random_state=seed)
    splits = list(splitter.split(frame.texto, frame.clasificacion))
    calibration_folds = pipeline.named_steps["classifier"].cv
    for train, _ in splits:
        counts = frame.iloc[train].clasificacion.value_counts()
        if len(counts) != 4 or counts.min() < calibration_folds:
            return {
                "cv_status": "not_feasible",
                "cv_reason": (
                    "Algún fold deja menos correos por clase que los "
                    f"{calibration_folds} folds de calibración interna."
                ),
                "cv_folds": None,
                "cv_f1_macro": None,
                "cv_f1_std": None,
                "cv_accuracy": None,
                "baseline_cv_f1_macro": None,
            }
    scoring = {"f1": "f1_macro", "accuracy": "accuracy"}
    scores = cross_validate(
        clone(pipeline),
        frame.texto,
        frame.clasificacion,
        cv=splits,
        scoring=scoring,
        n_jobs=1,
        error_score="raise",
    )
    baseline = cross_validate(
        build_pipeline("baseline", seed),
        frame.texto,
        frame.clasificacion,
        cv=splits,
        scoring=scoring,
        n_jobs=1,
        error_score="raise",
    )
    return {
        "cv_status": "exploratory",
        "cv_reason": "CV interna con ajustes previamente seleccionados; "
        "no es un test externo ni validación anidada de la búsqueda.",
        "cv_folds": folds,
        "cv_f1_macro": float(np.mean(scores["test_f1"])),
        "cv_f1_std": float(np.std(scores["test_f1"])),
        "cv_accuracy": float(np.mean(scores["test_accuracy"])),
        "baseline_cv_f1_macro": float(np.mean(baseline["test_f1"])),
    }


def evaluate_versions():
    """Verify all versions and 25 predictions without saving models."""
    config = load_config()
    source = ROOT / config["data_path"]
    corpus = load_data(source)
    test_path = ROOT / "data/test/correos_test_25.json"
    paths = [source, test_path]
    paths += [ROOT / "models" / f"modelo_clasificador_{s}.pkl" for s in SIZES]
    paths += [ROOT / "data/train" / f"correos_{s}.json" for s in SIZES]
    before = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in paths}
    rows = []
    for size in SIZES:
        LOGGER.info("Verificando y evaluando modelo de %s correos", size)
        pipeline, frame, _, _ = verify_artifact(size, corpus)
        predicted = pipeline.predict(frame.texto)
        row = {
            "correos": size,
            "model_sha256": before[f"models/modelo_clasificador_{size}.pkl"],
            "train_accuracy": float(
                accuracy_score(frame.clasificacion, predicted)
            ),
            "train_f1_macro": float(
                f1_score(frame.clasificacion, predicted, average="macro")
            ),
        }
        row.update(
            cross_validation(
                pipeline, frame, config["cv_folds"], config["seed"]
            )
        )
        summary, predictions = evaluate_new(
            test_path,
            ROOT / "models" / f"modelo_clasificador_{size}.pkl",
            source,
            ROOT / "results/metrics/training_summary.json",
            ROOT / "results/new_test_25" / f"modelo_clasificador_{size}",
            config["confidence_threshold"],
        )
        row.update(
            {
                "test_25_count": summary["n_test"],
                "test_25_review_count": int(
                    predictions.requiere_revision.sum()
                ),
                "test_25_mean_confidence_pct": float(
                    predictions.confianza_pct.mean()
                ),
                "test_25_accuracy": None,
                "test_25_f1_macro": None,
            }
        )
        rows.append(row)
    unchanged = all(
        file_hash(ROOT / name) == value for name, value in before.items()
    )
    if not unchanged:
        raise ValueError("Cambió un modelo o dataset durante la verificación.")
    output = {
        "models_and_datasets_unchanged": unchanged,
        "input_hashes": before,
        "versions": rows,
        "limits": [
            "Training metrics measure fit on known training examples only.",
            "Exploratory CV: shared settings tuned on overlapping data.",
            "Datasets are nested and do not isolate sample size causally.",
            "The 25 known tickets have no reviewed labels: no accuracy/F1.",
        ],
    }
    folder = ROOT / "results/metrics"
    save_json(folder / "version_evaluation.json", output)
    save_csv(
        pd.DataFrame(rows), folder / "version_evaluation.csv", index=False
    )
    plot_comparison(rows)
    print(
        pd.DataFrame(rows)[
            [
                "correos",
                "train_f1_macro",
                "cv_f1_macro",
                "baseline_cv_f1_macro",
                "test_25_count",
                "test_25_review_count",
            ]
        ].to_string(index=False)
    )
    return output


def plot_comparison(rows):
    """Plot available CV scores and baseline without fabricating scores."""
    available = [row for row in rows if row["cv_f1_macro"] is not None]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(
        [r["correos"] for r in available],
        [r["cv_f1_macro"] for r in available],
        yerr=[r["cv_f1_std"] for r in available],
        marker="o",
        capsize=4,
        label="SVM: F1 macro CV (media y desv.)",
    )
    ax.plot(
        [r["correos"] for r in available],
        [r["baseline_cv_f1_macro"] for r in available],
        marker="o",
        label="Baseline: clase mayoritaria",
    )
    ax.set(
        xlabel="Correos de entrenamiento",
        ylabel="F1 macro",
        title="Comparación interna exploratoria por versión",
        ylim=(0, 1.05),
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    image = ROOT / "documentacion/imagenes/comparacion_modelos_cv.png"
    fig.savefig(image, dpi=160)
    plt.close(fig)


def main():
    """Run the reproducible comparison with informative errors."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    try:
        evaluate_versions()
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit(f"Error al evaluar las versiones: {exc}") from exc


if __name__ == "__main__":
    main()
