"""Verify comparable dataset sizes and safe version selection."""

import joblib
import numpy as np
import pandas as pd
import pytest

from src.data_processing import CLASSES, combine_text
from src.evaluate_new import resolve_model, training_subset_for_model
from src.export_datasets import export_dataset
from src.model import build_pipeline, load_model, refit_pipeline
from src.train_versions import attach_training_manifest, nested_subsets
from src.utils import ROOT


@pytest.mark.parametrize("size", [None, 10, 100, 200, 300])
def test_training_selection_preserves_other_models(tmp_path, monkeypatch, size):
    """Train fixture models and verify only requested artifacts are replaced."""
    import json

    import src.train_versions as training
    from src.utils import load_config

    frame = corpus()
    source = tmp_path / "correos.json"
    source.write_text(frame.drop(columns="texto").to_json(orient="records"),
                      encoding="utf-8")
    for folder in ("models", "data/train", "results/metrics"):
        (tmp_path / folder).mkdir(parents=True)
    selected = training.SIZES if size is None else (size,)
    preserved = {}
    for other in set(training.SIZES) - set(selected):
        path = tmp_path / "models" / f"modelo_clasificador_{other}.pkl"
        path.write_bytes(b"modelo previo intacto")
        preserved[path] = path.read_bytes()
    settings = load_config()
    settings["data_path"] = str(source)
    monkeypatch.setattr(training, "ROOT", tmp_path)
    monkeypatch.setattr(training, "load_model", lambda _: build_pipeline("svm"))
    table = training.train_versions(settings, size=size)
    assert table.correos.tolist() == list(selected)
    for path, original in preserved.items():
        assert path.read_bytes() == original
    for count in selected:
        model = load_model(tmp_path / "models" / f"modelo_clasificador_{count}.pkl")
        assert model.training_sample_count_ == count
        dataset = tmp_path / "data/train" / f"correos_{count}.json"
        assert len(json.loads(dataset.read_text(encoding="utf-8"))) == count
    report = "model_versions" if size is None else f"model_versions_{size}"
    assert (tmp_path / "results/metrics" / f"{report}.json").exists()


def test_training_rejects_unsupported_size_before_loading(monkeypatch):
    """Reject invalid sizes before any model or dataset is accessed."""
    from src.train_versions import train_versions

    with pytest.raises(ValueError, match="10, 100, 200 o 300"):
        train_versions({}, size=25)


def corpus():
    """Build a 300-row fixture with the current class distribution."""
    counts = {
        "accesos": 70,
        "aplicaciones": 90,
        "infraestructura": 70,
        "otros": 70,
    }
    rows = [
        {
            "titulo": f"Ticket {label} {i}",
            "cuerpo": f"Detalle del caso {i}",
            "clasificacion": label,
        }
        for label, count in counts.items()
        for i in range(count)
    ]
    frame = pd.DataFrame(rows)
    frame["texto"] = [combine_text(r["titulo"], r["cuerpo"]) for r in rows]
    return frame


def test_subsets_have_exact_sizes_and_are_nested():
    """Every version must use the stated count and include all classes."""
    versions = nested_subsets(corpus())
    for size, frame in versions.items():
        assert len(frame) == size
        assert set(frame.clasificacion) == set(CLASSES)
        assert frame.clasificacion.value_counts().min() >= 2
    for smaller, larger in zip((10, 100, 200), (100, 200, 300)):
        assert set(versions[smaller].index) <= set(versions[larger].index)
    assert (
        versions[10].index.tolist()
        == nested_subsets(corpus())[10].index.tolist()
    )


def test_ten_ticket_svm_can_be_saved_and_verified(tmp_path):
    """Two-fold calibration must support the smallest four-class version."""
    all_rows = corpus()
    subset = nested_subsets(all_rows)[10]
    model = refit_pipeline(
        build_pipeline("svm"), subset.texto, subset.clasificacion
    )
    attach_training_manifest(model, subset, "fixture-source")
    path = tmp_path / "model.pkl"
    joblib.dump(model, path)
    loaded = load_model(path)
    assert loaded.training_sample_count_ == 10
    assert np.isclose(loaded.predict_proba([subset.texto.iloc[0]]).sum(), 1)
    assert (
        training_subset_for_model(loaded, all_rows).index.tolist()
        == subset.index.tolist()
    )
    changed = all_rows.copy()
    changed.loc[subset.index[0], "clasificacion"] = "invalid"
    with pytest.raises(ValueError, match="corpus cambió"):
        training_subset_for_model(loaded, changed)


def test_command_line_model_shortcuts():
    """Size and filename arguments must resolve to saved model files."""
    assert (
        resolve_model("100", "unused")
        == ROOT / "models/modelo_clasificador_100.pkl"
    )
    assert (
        resolve_model("modelo_clasificador_10.pkl", "unused")
        == ROOT / "models/modelo_clasificador_10.pkl"
    )


def test_export_preserves_training_order_and_fields(tmp_path):
    """The exported JSON must match the fitted records and their order."""
    import json

    subset = nested_subsets(corpus())[10]
    path = tmp_path / "correos_10.json"
    export_dataset(subset, path)
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) == 10
    assert all(
        set(row) == {"titulo", "cuerpo", "clasificacion"} for row in rows
    )
    assert [row["titulo"] for row in rows] == subset.titulo.tolist()


@pytest.mark.parametrize("size", [10, 100, 200, 300])
def test_delivered_model_matches_dataset_and_predicts_25(size):
    """Check real artifacts, four-class probabilities and no model mutation."""
    from src.data_processing import load_data
    from src.evaluate_new import assert_unseen, load_new_tickets
    from src.evaluate_versions import verify_artifact
    from src.utils import file_hash

    path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
    before = file_hash(path)
    corpus_frame = load_data(ROOT / "data/raw/correos.json")
    pipeline, subset, _, _ = verify_artifact(size, corpus_frame)
    testing = load_new_tickets(ROOT / "data/test/correos_test_25.json")
    assert_unseen(subset, testing)
    probabilities = pipeline.predict_proba(testing.texto)
    assert probabilities.shape == (25, 4)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    assert np.allclose(probabilities.sum(axis=1), 1)
    assert file_hash(path) == before


def test_smallest_version_reports_calibration_cv_limit():
    """Do not manufacture a CV score when inner calibration cannot fit."""
    from src.data_processing import load_data
    from src.evaluate_versions import cross_validation, verify_artifact

    frame = load_data(ROOT / "data/raw/correos.json")
    pipeline, subset, _, _ = verify_artifact(10, frame)
    result = cross_validation(pipeline, subset, folds=4, seed=42)
    assert result["cv_status"] == "not_feasible"
    assert result["cv_f1_macro"] is None
