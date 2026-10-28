"""Verify restart persistence, link isolation and concurrent history writes."""

from concurrent.futures import ThreadPoolExecutor

from app.persistent_history import HistoryStore, history_token


def test_reopen_restore_and_clear_only_the_requested_history(tmp_path):
    path = tmp_path / "history.sqlite3"
    first, second = history_token(), history_token()
    store = HistoryStore(path)
    store.append(first, {"titulo": "Cuenta bloqueada", "probabilidades": {"accesos": .9}})
    store.append(second, {"titulo": "Red caída", "probabilidades": {"infraestructura": .8}})
    restored = HistoryStore(path)
    assert restored.load(first)[0]["titulo"] == "Cuenta bloqueada"
    assert restored.load(second)[0]["titulo"] == "Red caída"
    assert restored.load(history_token()) == []
    restored.clear(first)
    assert HistoryStore(path).load(first) == []
    assert HistoryStore(path).load(second)[0]["titulo"] == "Red caída"
    assert restored.append(first, {"titulo": "Nuevo"})["id"] == 2


def test_parallel_writes_keep_unique_identifiers_and_retention(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    token = history_token()
    with ThreadPoolExecutor(max_workers=4) as executor:
        entries = list(executor.map(
            lambda number: store.append(token, {"titulo": str(number)}, limit=5),
            range(12),
        ))
    assert len({entry["id"] for entry in entries}) == 12
    assert [entry["id"] for entry in store.load(token)] == [8, 9, 10, 11, 12]


def test_interface_restores_history_in_a_new_session_with_the_same_link(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from src.utils import ROOT

    monkeypatch.setenv("HISTORY_DB_PATH", str(tmp_path / "history.sqlite3"))
    first = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30)
    first.query_params["historial"] = history_token()
    first.run()
    first.button(key="load_example").click().run()
    first.button(key="classify").click().run()
    token = first.query_params["historial"]
    assert len(first.session_state["prediction_history"]) == 1
    restored = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30)
    restored.query_params["historial"] = token
    restored.run()
    assert not restored.exception
    assert restored.session_state["prediction_history"][0]["modelo_correos"] == 300
    other = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30)
    other.query_params["historial"] = history_token()
    other.run()
    assert "prediction_history" not in other.session_state
    restored.button(key="clear_history").click().run()
    assert "prediction_history" not in restored.session_state
    assert not restored.exception
