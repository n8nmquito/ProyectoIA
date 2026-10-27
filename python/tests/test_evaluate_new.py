"""Ensure external evaluation stays separate and never fits the model."""

import json

import joblib
import pytest
from sklearn.pipeline import Pipeline

from src.data_processing import CLASSES, load_data
from src.evaluate_new import assert_unseen, evaluate_new, load_new_tickets
from src.model import build_pipeline
from src.utils import file_hash


def make_records(prefix, labelled=True):
    """Create one labelled ticket per category for isolated tests."""
    rows = [
        {
            "titulo": f"{prefix} {label}",
            "cuerpo": f"Consulta sobre {label}",
            "clasificacion": label,
        }
        for label in CLASSES
    ]
    if not labelled:
        for row in rows:
            row.pop("clasificacion")
    return rows


def write_dataset(path, records):
    """Save an isolated fixture dataset."""
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def test_rejects_training_overlap(tmp_path):
    """A known ticket cannot pass as an unseen evaluation example."""
    path = write_dataset(tmp_path / "data.json", make_records("Original"))
    frame = load_data(path)
    with pytest.raises(ValueError, match="presentes en entrenamiento"):
        assert_unseen(frame, frame)


def test_rejects_duplicates_in_new_test(tmp_path):
    """Duplicate test cases must not silently inflate or shrink results."""
    rows = make_records("Nuevo", labelled=False)
    path = write_dataset(tmp_path / "new.json", rows + [rows[0]])
    with pytest.raises(ValueError, match="duplicados"):
        load_new_tickets(path)


def test_evaluation_never_fits_or_changes_model(tmp_path, monkeypatch):
    """Predict without fitting or changing input files."""
    train_path = write_dataset(
        tmp_path / "train.json", make_records("Original")
    )
    test_path = write_dataset(
        tmp_path / "new.json", make_records("Nuevo", labelled=False)
    )
    train = load_data(train_path)
    model = build_pipeline().fit(train.texto, train.clasificacion)
    model_path = tmp_path / "model.pkl"
    joblib.dump(model, model_path)
    original_hash = file_hash(model_path)
    meta_path = tmp_path / "training_summary.json"
    meta_path.write_text(
        json.dumps(
            {
                "model_sha256": original_hash,
                "source_sha256": file_hash(train_path),
                "n_train": len(train),
            }
        ),
        encoding="utf-8",
    )

    def forbidden_fit(*args, **kwargs):
        """Fail immediately if evaluation attempts to train a pipeline."""
        raise AssertionError("Evaluation attempted to fit a model")

    monkeypatch.setattr(Pipeline, "fit", forbidden_fit)
    metrics, predictions = evaluate_new(
        test_path, model_path, train_path, meta_path, tmp_path / "results"
    )
    assert metrics["n_test"] == 4
    assert len(predictions) == 4
    assert not metrics["model_refitted"]
    assert metrics["exact_training_test_overlap"] == 0
    assert "accuracy" not in metrics
    assert "real" not in predictions.columns
    assert file_hash(model_path) == original_hash
    assert (tmp_path / "results/reporte.md").exists()


def test_input_rejects_expected_categories(tmp_path):
    """Inference inputs must contain title and body only."""
    path = write_dataset(tmp_path / "new.json", make_records("Nuevo"))
    with pytest.raises(ValueError, match="solo titulo y cuerpo"):
        load_new_tickets(path)
