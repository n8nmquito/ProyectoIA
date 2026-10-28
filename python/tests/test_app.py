"""Exercise the real Streamlit script with AppTest."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.model import load_model, predict_ticket

from src.utils import ROOT


def open_app():
    """Start the actual application in Streamlit's testing runtime."""
    return AppTest.from_file(
        str(ROOT / "app/app.py"), default_timeout=30
    ).run()


def test_app_rejects_invalid_input():
    """Empty form submission must show an error without crashing."""
    app = open_app()
    app.button(key="classify").click().run()
    assert len(app.error) == 1
    assert not app.exception


def test_app_loads_example():
    """The example button must fill both widgets."""
    app = open_app()
    app.button(key="load_example").click().run()
    assert app.text_input[0].value
    assert app.text_area[0].value
    assert not app.exception


def test_app_missing_model(monkeypatch):
    """A missing model must produce a helpful UI error."""
    original_stat = Path.stat

    def guarded_stat(path, *args, **kwargs):
        """Simulate a missing trained artifact without deleting real files."""
        if path.name == "modelo_clasificador_300.pkl":
            raise FileNotFoundError("simulado")
        return original_stat(path, *args, **kwargs)

    app = open_app()
    app.button(key="load_example").click().run()
    monkeypatch.setattr(Path, "stat", guarded_stat)
    app.button(key="classify").click().run()
    assert any("Falta el modelo" in error.value for error in app.error)
    assert not app.exception


def test_app_prediction():
    """The delivered model must produce a visible category in the actual UI."""
    app = open_app()
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    assert any(
        item.value == app.session_state["last_result"]["categoria"].capitalize()
        for item in app.subheader
    )
    assert not app.error
    assert not app.exception


@pytest.mark.parametrize("size", [10, 100, 200, 300])
def test_app_uses_selected_model(size):
    """The visible result must come from the exact selected artifact."""
    app = open_app()
    assert app.selectbox(key="model_size").value == 300
    app.selectbox(key="model_size").select(size).run()
    assert any(
        item.value == f"Modelo seleccionado: {size} correos"
        for item in app.subheader
    )
    assert not any("280" in item.value for item in app.info)
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    pipeline = load_model(ROOT / "models" / f"modelo_clasificador_{size}.pkl")
    expected = predict_ticket(
        pipeline, app.text_input[0].value, app.text_area[0].value,
    )
    assert any(
        item.label == "Términos TF-IDF"
        and item.value == str(len(pipeline.named_steps["tfidf"].vocabulary_))
        for item in app.metric
    )
    assert app.session_state["result_model_size"] == size
    assert app.session_state["last_result"]["probabilidades"] == pytest.approx(
        expected["probabilidades"]
    )
    assert not app.error
    assert not app.exception


def test_app_model_change_clears_previous_prediction():
    """Changing model must not relabel a result from another artifact."""
    app = open_app()
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    assert "last_result" in app.session_state
    app.selectbox(key="model_size").select(10).run()
    assert "last_result" not in app.session_state
    assert app.text_input[0].value
    assert app.text_area[0].value
    assert not app.exception


def test_session_history_survives_model_change_without_duplicate_reruns():
    """Only successful explicit predictions append independent history entries."""
    app = open_app()
    app.button(key="classify").click().run()
    assert "prediction_history" not in app.session_state
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    first = app.session_state["prediction_history"][0]
    app.run()
    assert len(app.session_state["prediction_history"]) == 1
    app.selectbox(key="model_size").select(100).run()
    app.button(key="classify").click().run()
    history = app.session_state["prediction_history"]
    assert [row["modelo_correos"] for row in history] == [300, 100]
    assert history[0] == first
    assert len(app.get("arrow_vega_lite_chart")) >= 2
    assert not app.exception


def test_clear_history_and_editing_input_do_not_export_stale_results():
    """Edited tickets invalidate the result; clearing history removes session rows."""
    app = open_app()
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    app.text_input(key="title").set_value("Otro incidente de red").run()
    assert "last_result" not in app.session_state
    assert len(app.session_state["prediction_history"]) == 1
    app.button(key="clear_history").click().run()
    assert "prediction_history" not in app.session_state
    assert not app.exception


def test_english_and_light_theme_preserve_model_and_session_results():
    """Presentation changes translate controls without pretending English training."""
    app = open_app()
    app.selectbox(key="model_size").select(100).run()
    app.button(key="load_example").click().run()
    app.button(key="classify").click().run()
    before = app.session_state["last_result"]
    before_title = app.text_input(key="title").value
    before_body = app.text_area(key="body").value
    app.selectbox(key="language").select("English").run()
    app.selectbox(key="theme").select("light").run()
    assert app.button(key="classify").label == "Classify"
    assert app.button(key="load_example").label == "Try an example"
    assert any("trained on Spanish tickets" in item.value for item in app.info)
    assert app.session_state["last_result"] == before
    assert app.selectbox(key="model_size").value == 100
    assert app.text_input(key="title").value == before_title
    assert app.text_area(key="body").value == before_body
    assert not any("Session State API" in item.value for item in app.warning)
    assert len(app.session_state["prediction_history"]) == 1
    assert not app.exception
