"""Train comparable, nested models with 10, 100, 200 and 300 tickets."""

import argparse
import json
import logging

import joblib
import numpy as np
import pandas as pd

from src.data_processing import CLASSES, load_data, ticket_fingerprint
from src.export_datasets import export_dataset
from src.model import load_model, refit_pipeline
from src.utils import ROOT, file_hash, load_config, project_path, save_json

LOGGER = logging.getLogger(__name__)
SIZES = (10, 100, 200, 300)


def nested_subsets(frame, seed=42):
    """Select nested stratified subsets covering every class at every size."""
    if len(frame) != 300:
        raise ValueError("Se requieren exactamente 300 correos únicos.")
    rng = np.random.default_rng(seed)
    order = {
        label: rng.permutation(frame.index[frame.clasificacion == label])
        for label in CLASSES
    }
    small = {"accesos": 3, "aplicaciones": 3, "infraestructura": 2, "otros": 2}
    subsets = {}
    for size in SIZES:
        if size == 300:
            indices = frame.index.tolist()
        else:
            quota = small if size == 10 else dict.fromkeys(CLASSES, size // 4)
            if any(
                len(order[label]) < count for label, count in quota.items()
            ):
                raise ValueError("No hay suficientes ejemplos por categoría.")
            indices = sorted(
                int(i)
                for label, count in quota.items()
                for i in order[label][:count]
            )
        subsets[size] = frame.loc[indices].copy()
    return subsets


def attach_training_manifest(model, subset, source_hash):
    """Embed exact subset identity in the model without extra corpus files."""
    model.training_sample_count_ = len(subset)
    model.training_class_counts_ = (
        subset.clasificacion.value_counts().to_dict()
    )
    model.training_row_indices_ = subset.index.tolist()
    model.training_text_fingerprints_ = subset.texto.map(
        ticket_fingerprint
    ).tolist()
    model.training_labels_ = subset.clasificacion.tolist()
    model.training_source_sha256_ = source_hash
    return model


def train_versions(config):
    """Fit all four sizes with one selected algorithm and configuration."""
    source = project_path(config["data_path"])
    frame = load_data(source)
    subsets = nested_subsets(frame, config["seed"])
    template = load_model(project_path(config["model_path"]))
    classifier = template.named_steps["classifier"]
    calibration_folds = config["model"]["calibration_folds"]
    if getattr(classifier, "cv", None) != calibration_folds:
        raise ValueError(
            "Primero ejecuta src.train con la calibración configurada."
        )
    if any(
        subset.clasificacion.value_counts().min() < calibration_folds
        for subset in subsets.values()
    ):
        raise ValueError(
            "Las muestras pequeñas no admiten tantos folds de calibración."
        )
    source_hash = file_hash(source)
    rows = []
    for size, subset in subsets.items():
        LOGGER.info("Entrenando versión de %d correos", size)
        model = refit_pipeline(template, subset.texto, subset.clasificacion)
        attach_training_manifest(model, subset, source_hash)
        path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
        joblib.dump(model, path)
        dataset_path = ROOT / "data/train" / f"correos_{size}.json"
        export_dataset(subset, dataset_path)
        rows.append(
            {
                "correos": size,
                "archivo": str(path.relative_to(ROOT)),
                "dataset": str(dataset_path.relative_to(ROOT)),
                "sha256": file_hash(path),
                "clases": model.training_class_counts_,
            }
        )
    summary_path = ROOT / "results/metrics/training_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("source_sha256") == source_hash and summary.get(
            "n_train"
        ) == len(frame):
            summary["model_sha256"] = file_hash(
                project_path(config["model_path"])
            )
            summary["config"]["model_path"] = config["model_path"]
            save_json(summary_path, summary)
    save_json(
        ROOT / "results/metrics/model_versions.json",
        {
            "source_sha256": source_hash,
            "seed": config["seed"],
            "algorithm": (
                "TF-IDF + LinearSVC with sigmoid calibration, "
                f"cv={calibration_folds}"
            ),
            "parameters": {
                key: value
                for key, value in template.get_params().items()
                if key
                in {
                    "classifier__estimator__C",
                    "classifier__estimator__class_weight",
                    "tfidf__min_df",
                }
            },
            "selection": (
                "Nested per-class random order; same settings for all sizes."
            ),
            "versions": rows,
            "limitation": (
                "10 tickets is a demonstration, not a reliable model."
            ),
        },
    )
    table = pd.DataFrame(rows)
    table.to_csv(ROOT / "results/metrics/model_versions.csv", index=False)
    return table


def main():
    """Expose repeatable training of the four saved size variants."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    try:
        table = train_versions(load_config(args.config))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error al entrenar versiones: {exc}\n")
    print(table[["correos", "archivo"]].to_string(index=False))


if __name__ == "__main__":
    main()
