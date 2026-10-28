"""Verify export integrity, formula safety and bounded session retention."""

import csv
import io

from app.session_results import HISTORY_LIMIT, csv_bytes, remember_prediction


def sample_result():
    return {
        "categoria": "accesos", "confianza": 0.7, "requiere_revision": False,
        "probabilidades": {"accesos": 0.7, "aplicaciones": 0.1,
                           "infraestructura": 0.1, "otros": 0.1},
    }


def test_export_preserves_unicode_multiline_probabilities_and_escapes_formulas():
    state = {}
    result = sample_result()
    remember_prediction(state, '=HYPERLINK("malicioso")',
                        'Descripción, con comillas "y"\ndos líneas', 300, result)
    result["probabilidades"]["accesos"] = 0.1
    rows = list(csv.DictReader(io.StringIO(
        csv_bytes(state["prediction_history"]).decode("utf-8-sig"))))
    assert len(rows) == 1
    assert rows[0]["titulo"].startswith("'=HYPERLINK")
    assert rows[0]["cuerpo"] == 'Descripción, con comillas "y"\ndos líneas'
    assert float(rows[0]["p_accesos"]) == 0.7
    assert float(rows[0]["confianza"]) == 0.7
    assert int(rows[0]["modelo_correos"]) == 300


def test_retention_drops_oldest_entries_without_reusing_identifiers():
    state = {}
    for index in range(HISTORY_LIMIT + 2):
        remember_prediction(state, str(index), "Descripción", 100, sample_result())
    assert len(state["prediction_history"]) == HISTORY_LIMIT
    assert state["prediction_history"][0]["id"] == 3
    assert state["prediction_history"][-1]["id"] == HISTORY_LIMIT + 2
    assert state["last_entry"] == state["prediction_history"][-1]
