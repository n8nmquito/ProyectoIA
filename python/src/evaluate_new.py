"""Predict categories from title and body without answer files."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data_processing import combine_text, load_data, ticket_fingerprint
from src.model import load_model, predict_ticket
from src.utils import (
    ROOT,
    file_hash,
    load_config,
    project_path,
    save_csv,
    save_json,
)


def read_json(path):
    """Read JSON with an informative error."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer {path}: {exc}") from exc


def load_new_tickets(path):
    """Require title and body only; reject labels and normalized duplicates."""
    rows = read_json(path)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Se requiere una lista no vacía de correos.")
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != {"titulo", "cuerpo"}:
            raise ValueError(f"Correo {index}: usar solo titulo y cuerpo.")
    frame = pd.DataFrame(rows)
    frame["texto"] = [combine_text(r["titulo"], r["cuerpo"]) for r in rows]
    if frame.texto.duplicated().any():
        raise ValueError("El test contiene duplicados normalizados.")
    return frame


def assert_unseen(training, testing):
    """Reject exact normalized overlap with the training corpus."""
    overlap = set(training.texto) & set(testing.texto)
    if overlap:
        raise ValueError(
            f"Hay {len(overlap)} tickets presentes en entrenamiento."
        )


def training_subset_for_model(model, corpus):
    """Recover and verify the exact training subset embedded in a version."""
    indices = model.training_row_indices_
    if len(set(indices)) != len(indices):
        raise ValueError(
            "El modelo contiene índices de entrenamiento repetidos."
        )
    try:
        subset = corpus.loc[indices].copy()
    except KeyError as exc:
        raise ValueError(
            "Faltan correos usados por esta versión del modelo."
        ) from exc
    if (
        len(subset) != model.training_sample_count_
        or subset.texto.map(ticket_fingerprint).tolist()
        != model.training_text_fingerprints_
        or subset.clasificacion.tolist() != model.training_labels_
    ):
        raise ValueError(
            "El corpus cambió respecto a esta versión del modelo."
        )
    return subset


def resolve_model(value, default_path):
    """Resolve a size shortcut, a model filename or an explicit model path."""
    if value is None:
        return project_path(default_path)
    if value.isdigit():
        return ROOT / "models" / f"modelo_clasificador_{value}.pkl"
    path = Path(value)
    if len(path.parts) == 1 and path.suffix == ".pkl":
        return ROOT / "models" / path
    return project_path(value)


def evaluate_new(
    test_path,
    model_path,
    training_path,
    metadata_path,
    output_dir,
    threshold=0.60,
):
    """Predict categories and confidence without fitting the model."""
    test_path, model_path = Path(test_path), Path(model_path)
    training_path, output_dir = Path(training_path), Path(output_dir)
    training, testing = load_data(training_path), load_new_tickets(test_path)
    assert_unseen(training, testing)
    model_hash, training_hash = file_hash(model_path), file_hash(training_path)
    test_hash = file_hash(test_path)
    model = load_model(model_path)
    if hasattr(model, "training_row_indices_"):
        training = training_subset_for_model(model, training)
    else:
        metadata = read_json(metadata_path)
        if metadata.get("model_sha256") != model_hash:
            raise ValueError(
                "El modelo no coincide con training_summary.json."
            )
        if metadata.get("source_sha256") != training_hash:
            raise ValueError("El corpus no coincide con el usado al entrenar.")
        if metadata.get("n_train") != len(training):
            raise ValueError(
                "Se requiere el modelo final del corpus completo."
            )
    rows = []
    for index, row in testing.iterrows():
        result = predict_ticket(model, row.titulo, row.cuerpo, threshold)
        detail = {
            "caso": index + 1,
            "titulo": row.titulo,
            "cuerpo": row.cuerpo,
            "predicha": result["categoria"],
            "confianza_pct": 100 * result["confianza"],
            "requiere_revision": result["requiere_revision"],
        }
        detail.update(
            {
                f"prob_{label}_pct": 100 * probability
                for label, probability in result["probabilidades"].items()
            }
        )
        rows.append(detail)
    predictions = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "mode": "predictions_only",
        "model_refitted": False,
        "n_training": len(training),
        "n_test": len(testing),
        "model_sha256": model_hash,
        "model_path": str(model_path),
        "test_sha256": test_hash,
        "exact_training_test_overlap": 0,
    }
    report = [
        "# Prueba de correos nuevos",
        "",
        f"{len(testing)} entradas con solo título y cuerpo. "
        f"Modelo entrenado previamente con {len(training)} correos.",
        "El script predice; no reentrena ni añade estos correos al corpus.",
    ]
    report.append(
        "Se muestran categorías predichas y confianza. Sin respuestas "
        "esperadas no se calculan accuracy ni F1 en esta prueba."
    )
    report.extend(
        [
            "",
            "## Alcance",
            "",
            "Estos 25 correos son sintéticos del mismo generador que parte "
            "del entrenamiento. No tener duplicados exactos no garantiza "
            "independencia "
            "semántica. Esta prueba pequeña no demuestra "
            "ausencia de sobreajuste; se necesita evidencia adicional con "
            "tickets "
            "reales y etiquetas revisadas por otras personas.",
        ]
    )
    if (
        file_hash(model_path) != model_hash
        or file_hash(training_path) != training_hash
        or file_hash(test_path) != test_hash
    ):
        raise ValueError("Un archivo de entrada cambió durante la prueba.")
    path = save_csv(
        predictions,
        output_dir / "predicciones.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary["predictions_csv"] = path.name
    save_json(output_dir / "resumen.json", summary)
    (output_dir / "reporte.md").write_text("\n".join(report), encoding="utf-8")
    return summary, predictions


def main():
    """Run prediction using only title and body as inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    parser.add_argument("--data", default="data/test/correos_test_25.json")
    parser.add_argument(
        "--model",
        default=None,
        help="Elegir 10, 100, 200, 300 o la ruta de un modelo .pkl.",
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        model_path = resolve_model(args.model, config["model_path"])
        output = (
            project_path(args.output)
            if args.output
            else ROOT / "results/new_test_25" / model_path.stem
        )
        summary, predictions = evaluate_new(
            project_path(args.data),
            model_path,
            project_path(config["data_path"]),
            ROOT / "results/metrics/training_summary.json",
            output,
            config["confidence_threshold"],
        )
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error en la prueba: {exc}\n")
    print(f"Modelo: {model_path.name}")
    print(f"Modelo entrenado con {summary['n_training']} correos.")
    print(f"Nuevos: {summary['n_test']}; entrada: título y cuerpo.")
    columns = ["caso", "titulo", "predicha", "confianza_pct", "requiere_revision"]
    print(predictions[columns].to_string(index=False, float_format="%.1f"))
    pending = predictions.loc[predictions["requiere_revision"]]
    print(f"\nCorreos que requieren revisión: {len(pending)}")
    for row in pending.itertuples(index=False):
        print("\n" + "=" * 70)
        print(
            f"Caso {row.caso} | Categoría sugerida: {row.predicha} | "
            f"Confianza: {row.confianza_pct:.1f} %"
        )
        print(f"Título: {row.titulo}")
        print(f"Cuerpo:\n{row.cuerpo}")
    print(f"Resultados: {output}")
    print("El modelo y los datos de entrenamiento no se modificaron.")


if __name__ == "__main__":
    main()
