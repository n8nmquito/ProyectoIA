"""Prevent invented or mismatched reference labels from producing metrics."""

import json

import pytest

from src.evaluate_reviewed import evaluate_reviewed, prepare_review


def test_reference_stays_separate_and_blank(tmp_path):
    """Preparation must preserve the unlabeled input and refuse overwrite."""
    data = [
        {"titulo": "Cuenta bloqueada", "cuerpo": "No puedo iniciar sesión"}
    ]
    source, reference = tmp_path / "input.json", tmp_path / "labels.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    before = source.read_bytes()
    assert prepare_review(source, reference) == 1
    assert source.read_bytes() == before
    assert json.loads(reference.read_text())[0]["clasificacion"] is None
    with pytest.raises(ValueError, match="no se sobrescribe"):
        prepare_review(source, reference)


def test_unreviewed_labels_cannot_produce_metrics(tmp_path):
    """Blank human labels must fail before loading or evaluating a model."""
    source, reference = tmp_path / "input.json", tmp_path / "labels.json"
    source.write_text(
        json.dumps([{"titulo": "Consulta", "cuerpo": "Ayuda con acceso"}])
    )
    prepare_review(source, reference)
    with pytest.raises(ValueError, match="revisión humana"):
        evaluate_reviewed(
            source,
            reference,
            tmp_path / "unused.pkl",
            tmp_path,
            "Revisor de prueba",
        )


def test_mismatched_reference_is_rejected(tmp_path):
    """A label sheet for a different email must not be accepted."""
    source, reference = tmp_path / "input.json", tmp_path / "labels.json"
    source.write_text(
        json.dumps([{"titulo": "Consulta", "cuerpo": "Ayuda con acceso"}])
    )
    reference.write_text(
        json.dumps(
            [
                {
                    "titulo": "Otro caso",
                    "cuerpo": "Ayuda con acceso",
                    "clasificacion": "accesos",
                }
            ]
        )
    )
    with pytest.raises(ValueError, match="no coincide"):
        evaluate_reviewed(
            source,
            reference,
            tmp_path / "unused.pkl",
            tmp_path,
            "Revisor de prueba",
        )


def test_reviewed_metrics_are_regression_and_never_refit(
    tmp_path, monkeypatch
):
    """Compute reviewed metrics while preserving the model and scope label."""
    import joblib
    from sklearn.pipeline import Pipeline

    from src.data_processing import CLASSES, combine_text
    from src.model import build_pipeline
    from src.utils import file_hash

    rows = [
        {"titulo": label, "cuerpo": "Consulta sobre " + label}
        for label in CLASSES
    ]
    reference_rows = [
        {**row, "clasificacion": label} for row, label in zip(rows, CLASSES)
    ]
    source, reference = tmp_path / "input.json", tmp_path / "labels.json"
    source.write_text(json.dumps(rows))
    reference.write_text(json.dumps(reference_rows))
    model = build_pipeline().fit(
        [combine_text(row["titulo"], row["cuerpo"]) for row in rows], CLASSES
    )
    path = tmp_path / "model.pkl"
    joblib.dump(model, path)
    before = file_hash(path)

    def forbidden_fit(*args, **kwargs):
        """Evaluation must never train a model."""
        raise AssertionError("No entrenar al evaluar")

    monkeypatch.setattr(Pipeline, "fit", forbidden_fit)
    report = evaluate_reviewed(
        source, reference, path, tmp_path, "Revisor ficticio de test"
    )
    assert report["independent_test"] is False
    assert report["evaluation_scope"] == "known_cases_regression"
    assert report["n_test"] == 4
    assert file_hash(path) == before
