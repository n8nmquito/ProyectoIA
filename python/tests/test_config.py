"""Check configurable model settings and consistent history retention."""

import pytest
import yaml

from app.persistent_history import HistoryStore, history_token
from app.session_results import remember_prediction
from src.model import build_pipeline
from src.utils import load_config


def write_config(path, settings):
    """Save a partial configuration overriding the project defaults."""
    path.write_text(yaml.safe_dump(settings), encoding="utf-8")
    return path


def test_model_overrides_reach_the_estimators(tmp_path):
    path = write_config(tmp_path / "custom.yaml", {
        "model": {"logistic_max_iter": 345, "calibration_folds": 3,
                  "svm_c": 2.5, "svm_class_weight": "balanced"},
        "tfidf": {"ngram_range": [1, 3], "sublinear_tf": False,
                  "min_df": 2, "max_df": 0.9},
    })
    settings = load_config(path)
    logistic = build_pipeline(config=settings)
    svm = build_pipeline("svm", config=settings)
    assert logistic.named_steps["classifier"].max_iter == 345
    assert svm.named_steps["classifier"].cv == 3
    assert svm.named_steps["classifier"].estimator.C == 2.5
    assert svm.named_steps["classifier"].estimator.class_weight == "balanced"
    assert svm.named_steps["tfidf"].min_df == 2
    assert svm.named_steps["tfidf"].max_df == 0.9
    assert logistic.named_steps["tfidf"].ngram_range == (1, 3)
    assert logistic.named_steps["tfidf"].sublinear_tf is False
    assert logistic.named_steps["tfidf"].strip_accents == "unicode"


@pytest.mark.parametrize("override", [
    {"history_limit": 0},
    {"history_limit": True},
    {"model": {"calibration_folds": 1}},
    {"model": {"logistic_max_iter": -1}},
    {"model": {"svm_c": 0}},
    {"model": {"svm_class_weight": "invalid"}},
    {"tfidf": {"min_df": 0}},
    {"tfidf": {"max_df": 2.0}},
    {"tfidf": {"ngram_range": [3, 1]}},
    {"tfidf": {"sublinear_tf": "false"}},
    {"tfidf": {"strip_accents": "invalid"}},
])
def test_invalid_settings_fail_before_training(tmp_path, override):
    with pytest.raises(ValueError):
        load_config(write_config(tmp_path / "invalid.yaml", override))


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
def test_invalid_history_environment_is_informative(monkeypatch, value):
    monkeypatch.setenv("HISTORY_LIMIT", value)
    with pytest.raises(ValueError, match="entero positivo"):
        load_config()


def test_history_environment_controls_memory_and_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("HISTORY_LIMIT", "2")
    settings = load_config(write_config(
        tmp_path / "custom.yaml", {"history_limit": 8}
    ))
    assert settings["history_limit"] == 2
    state = {}
    store = HistoryStore(tmp_path / "history.sqlite3")
    token = history_token()
    for index in range(4):
        remember_prediction(state, str(index), "Descripción", 300,
                            {"categoria": "accesos"}, store, token)
    assert [row["id"] for row in state["prediction_history"]] == [3, 4]
    assert store.load(token) == state["prediction_history"]


def test_relative_config_resolves_from_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config("config.yaml") == load_config()
