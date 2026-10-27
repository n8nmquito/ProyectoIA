"""Export the exact records used to train each saved model version."""

import argparse

from src.data_processing import load_data
from src.evaluate_new import training_subset_for_model
from src.model import load_model
from src.utils import ROOT, load_config, project_path, save_json


def export_dataset(frame, path):
    """Save original fields in training order, without internal features."""
    records = frame[["titulo", "cuerpo", "clasificacion"]].to_dict(
        orient="records"
    )
    save_json(path, records)


def export_saved_datasets(config):
    """Recover the recorded training subsets without resampling or fitting."""
    corpus = load_data(project_path(config["data_path"]))
    exported = []
    for size in (10, 100, 200, 300):
        model = load_model(ROOT / "models" / f"modelo_clasificador_{size}.pkl")
        subset = training_subset_for_model(model, corpus)
        if len(subset) != size:
            raise ValueError(f"El modelo {size} no contiene {size} registros.")
        path = ROOT / "data/train" / f"correos_{size}.json"
        export_dataset(subset, path)
        exported.append((size, path))
    return exported


def main():
    """Run the export without changing saved models."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    try:
        exported = export_saved_datasets(load_config(args.config))
    except (ValueError, OSError, KeyError, AttributeError) as exc:
        parser.exit(1, f"Error al separar datasets: {exc}\n")
    for size, path in exported:
        print(f"{size} correos: {path}")


if __name__ == "__main__":
    main()
