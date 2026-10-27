"""Pipeline, persistence and probability behavior tests."""

import joblib
import numpy as np
import pytest

from src.model import (
    build_pipeline,
    load_model,
    predict_ticket,
    refit_pipeline,
)
from src.utils import save_csv


@pytest.fixture
def fitted_model():
    """Train a tiny isolated pipeline for unit tests."""
    texts = [
        "usuario bloqueado acceso cuenta",
        "error aplicación orden factura",
        "red servidor internet conexión",
        "capacitación consulta reunión",
    ] * 4
    labels = ["accesos", "aplicaciones", "infraestructura", "otros"] * 4
    return build_pipeline().fit(texts, labels)


def test_probabilities_and_persistence(fitted_model, tmp_path):
    """Persistence must preserve four normalized probabilities."""
    path = tmp_path / "model.pkl"
    joblib.dump(fitted_model, path)
    result = predict_ticket(
        load_model(path), "Usuario bloqueado", "Acceso a mi cuenta"
    )
    assert len(result["probabilidades"]) == 4
    assert np.isclose(sum(result["probabilidades"].values()), 1)
    assert all(0 <= p <= 1 for p in result["probabilidades"].values())
    assert result["categoria"] == "accesos"


def test_unknown_vocabulary_requires_review(fitted_model):
    """Unseen-only tokens must trigger manual review."""
    result = predict_ticket(fitted_model, "xyzabc", "qwertyzxcv")
    assert result["requiere_revision"]
    assert result["sin_vocabulario"]


def test_missing_model(tmp_path):
    """A missing artifact must produce an actionable error."""
    with pytest.raises(ValueError, match="Entrena de nuevo"):
        load_model(tmp_path / "missing.pkl")


def test_full_refit_uses_added_records_without_mutating_old_model(
    fitted_model,
):
    """Use every record for refitting and preserve the evaluation model."""
    texts = ["usuario bloqueado", "error factura", "red servidor", "consulta"]
    labels = ["accesos", "aplicaciones", "infraestructura", "otros"]
    texts.append("vocabularioexclusivofinal")
    labels.append("accesos")
    final = refit_pipeline(fitted_model, texts, labels)
    assert final.training_sample_count_ == 5
    assert final.training_class_counts_["accesos"] == 2
    assert (
        "vocabularioexclusivofinal" in final.named_steps["tfidf"].vocabulary_
    )
    assert "vocabularioexclusivofinal" not in (
        fitted_model.named_steps["tfidf"].vocabulary_
    )


def test_locked_csv_gets_a_new_filename(tmp_path, monkeypatch):
    """A spreadsheet lock must preserve the old report and save a new one."""
    import pandas as pd

    target = tmp_path / "report.csv"
    target.write_text("old report", encoding="utf-8")
    original = pd.DataFrame.to_csv

    def write_with_lock(frame, path, **kwargs):
        """Simulate Excel holding the target open on Windows."""
        if path == target:
            raise PermissionError("simulated lock")
        return original(frame, path, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", write_with_lock)
    actual = save_csv(pd.DataFrame({"score": [0.9]}), target, index=False)
    assert actual != target
    assert actual.exists()
    assert target.read_text(encoding="utf-8") == "old report"
    assert pd.read_csv(actual).score.iloc[0] == 0.9
