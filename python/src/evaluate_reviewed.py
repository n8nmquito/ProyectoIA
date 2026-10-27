"""Evaluate the existing test cases only after human label review."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data_processing import CLASSES, combine_text
from src.evaluate import evaluate_model
from src.evaluate_new import load_new_tickets
from src.model import load_model
from src.utils import ROOT, file_hash, save_json


def prepare_review(test_path, reference_path):
    """Create a separate blank label sheet without changing the test JSON."""
    reference_path = Path(reference_path)
    if reference_path.exists():
        raise ValueError("La hoja de revisión ya existe; no se sobrescribe.")
    frame = load_new_tickets(test_path)
    rows = [
        {"titulo": row.titulo, "cuerpo": row.cuerpo, "clasificacion": None}
        for row in frame.itertuples()
    ]
    save_json(reference_path, rows)
    return len(rows)


def evaluate_reviewed(
    test_path, reference_path, model_path, output_dir, reviewer
):
    """Measure known-case regression, never claim an independent test."""
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError(
            "Indica quién revisó las etiquetas; no usar el modelo como revisor."
        )
    testing = load_new_tickets(test_path)
    try:
        reference = json.loads(
            Path(reference_path).read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "No se pudo leer la hoja de etiquetas revisadas."
        ) from exc
    if not isinstance(reference, list) or len(reference) != len(testing):
        raise ValueError(
            "Las etiquetas deben cubrir exactamente los mismos correos."
        )
    labels = []
    for index, (row, expected) in enumerate(
        zip(reference, testing.itertuples()), 1
    ):
        if not isinstance(row, dict) or set(row) != {
            "titulo",
            "cuerpo",
            "clasificacion",
        }:
            raise ValueError(f"Fila {index}: formato de referencia inválido.")
        if (row["titulo"], row["cuerpo"]) != (
            expected.titulo,
            expected.cuerpo,
        ):
            raise ValueError(
                f"Fila {index}: el correo de referencia no coincide con el test."
            )
        if row["clasificacion"] not in CLASSES:
            raise ValueError(
                f"Fila {index}: etiqueta pendiente o inválida; requiere revisión humana."
            )
        labels.append(row["clasificacion"])
    frame = pd.DataFrame({"clasificacion": labels})
    frame["texto"] = [
        combine_text(row.titulo, row.cuerpo) for row in testing.itertuples()
    ]
    original_hash = file_hash(model_path)
    model = load_model(model_path)
    result = evaluate_model(model, frame)
    if file_hash(model_path) != original_hash:
        raise ValueError("El modelo cambió durante la evaluación.")
    result.update(
        {
            "evaluation_scope": "known_cases_regression",
            "independent_test": False,
            "human_reviewer": reviewer.strip(),
            "reference_sha256": file_hash(reference_path),
            "test_sha256": file_hash(test_path),
            "model_sha256": original_hash,
            "training_samples": getattr(model, "training_sample_count_", None),
            "limitation": "Casos previamente inspeccionados durante el desarrollo; no demuestran generalización ni ausencia de sobreajuste.",
        }
    )
    save_json(Path(output_dir) / "reviewed_regression_metrics.json", result)
    return result


def main():
    """Prepare human review or evaluate the same known cases explicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument(
        "--data", default=str(ROOT / "data/test/correos_test_25.json")
    )
    parser.add_argument(
        "--reference",
        default=str(ROOT / "data/evaluation/correos_para_revision.json"),
    )
    parser.add_argument(
        "--model", default=str(ROOT / "models/modelo_clasificador_300.pkl")
    )
    parser.add_argument(
        "--output", default=str(ROOT / "results/reviewed_regression")
    )
    parser.add_argument("--reviewer", default="")
    args = parser.parse_args()
    try:
        if args.prepare:
            count = prepare_review(args.data, args.reference)
            print(
                f"Hoja creada con {count} correos y etiquetas vacías para revisión humana."
            )
        else:
            report = evaluate_reviewed(
                args.data,
                args.reference,
                args.model,
                args.output,
                args.reviewer,
            )
            print(
                f"Regresión conocida: F1 macro {report['f1_macro']:.4f}; accuracy {report['accuracy']:.4f}."
            )
            print(report["limitation"])
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(1, f"Error en la revisión: {exc}\n")


if __name__ == "__main__":
    main()
