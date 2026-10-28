"""Match evaluation reports to artifacts and keep model series separate."""

import json
import shutil

import pytest

from src.data_processing import load_data
from src.evaluate_versions import verify_artifact
from src.utils import ROOT, file_hash, load_config


@pytest.mark.parametrize("primary_is_corrupt", [False, True])
def test_portal_reads_only_metrics_for_the_matching_model(
    tmp_path, monkeypatch, primary_is_corrupt
):
    """Find a matching production report despite an older or broken report."""
    from app import app as portal

    model = tmp_path / "models/modelo_clasificador_300.pkl"
    model.parent.mkdir()
    model.write_bytes(b"synthetic hash fixture, not a pickle")
    reference = tmp_path / "results/metrics/version_evaluation.json"
    reference.parent.mkdir(parents=True)
    reference.write_text(
        "invalid-json"
        if primary_is_corrupt
        else json.dumps(
            {
                "versions": [
                    {
                        "correos": 300,
                        "model_sha256": "old-model-hash",
                        "cv_f1_macro": 0.99,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    production = (
        tmp_path / "results/produccion/metrics/version_evaluation.json"
    )
    production.parent.mkdir(parents=True)
    row = {
        "correos": 300,
        "model_sha256": file_hash(model),
        "cv_f1_macro": 0.75,
    }
    production.write_text(json.dumps({"versions": [row]}), encoding="utf-8")
    monkeypatch.setattr(portal, "ROOT", tmp_path)
    assert portal.read_version_metrics(300) == row
    assert portal.read_version_metrics(100) is None
    row["model_sha256"] = "different-model"
    production.write_text(json.dumps({"versions": [row]}), encoding="utf-8")
    assert portal.read_version_metrics(300) is None


def test_artifact_can_be_verified_in_another_directory(tmp_path):
    """Check the selected model directory against the exact dataset."""
    source = ROOT / "models/modelo_clasificador_300.pkl"
    target = tmp_path / source.name
    shutil.copyfile(source, target)
    corpus = load_data(ROOT / "data/raw/correos.json")
    _, subset, actual_path, _ = verify_artifact(300, corpus, tmp_path)
    assert actual_path == target
    assert len(subset) == 300
    assert file_hash(source) == file_hash(target)


def test_separate_evaluation_keeps_reference_report_and_model(
    tmp_path, monkeypatch
):
    """Write a new series report without replacing artifacts or references."""
    from src import evaluate_versions as evaluation

    config = load_config()
    paths = [
        "config.yaml",
        "data/raw/correos.json",
        "data/test/correos_test_25.json",
        "data/train/correos_10.json",
        "models/modelo_clasificador_10.pkl",
    ]
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    reference = tmp_path / "results/metrics/version_evaluation.json"
    reference.parent.mkdir(parents=True)
    reference.write_text('{"reference": true}', encoding="utf-8")
    original_report = reference.read_bytes()
    model_path = tmp_path / "models/modelo_clasificador_10.pkl"
    original_hash = file_hash(model_path)
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation, "SIZES", (10,))
    monkeypatch.setattr(evaluation, "load_config", lambda: config)
    output = tmp_path / "results/produccion"
    result = evaluation.evaluate_versions(tmp_path / "models", output)
    assert reference.read_bytes() == original_report
    assert file_hash(model_path) == original_hash
    assert result["models_and_datasets_unchanged"] is True
    assert result["versions"][0]["model_sha256"] == original_hash
    assert result["versions"][0]["cv_status"] == "not_feasible"
    assert (output / "metrics/version_evaluation.json").is_file()
    assert (output / "metrics/version_evaluation.csv").is_file()
    assert (output / "figures/comparacion_modelos_cv.png").is_file()
