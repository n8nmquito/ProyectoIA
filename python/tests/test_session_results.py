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
                        'Descripción; con comillas "y", acentos\ndos líneas', 300, result)
    result["probabilidades"]["accesos"] = 0.1
    data = csv_bytes(state["prediction_history"])
    assert data.startswith(b"\xef\xbb\xbfsep=;\r\n")
    text = data.decode("utf-8-sig").split("\r\n", 1)[1]
    rows = list(csv.DictReader(io.StringIO(text, newline=""), delimiter=";"))
    assert len(rows) == 1
    assert rows[0]["titulo"].startswith("'=HYPERLINK")
    assert rows[0]["cuerpo"] == 'Descripción; con comillas "y", acentos\ndos líneas'
    assert float(rows[0]["p_accesos"]) == 0.7
    assert float(rows[0]["confianza"]) == 0.7
    assert int(rows[0]["modelo_correos"]) == 300


def test_excel_export_keeps_multiple_long_emails_in_separate_records():
    state = {}
    for index in range(2):
        remember_prediction(state, f"Correo {index}",
                            "Párrafo uno; con separador.\n\nPárrafo dos, con coma.",
                            300, sample_result())
    text = csv_bytes(state["prediction_history"]).decode("utf-8-sig")
    stream = io.StringIO(text, newline="")
    assert stream.readline() == "sep=;\r\n"
    reader = csv.DictReader(stream, delimiter=";")
    rows = list(reader)
    assert len(reader.fieldnames) == 12
    assert len(rows) == 2
    assert [row["titulo"] for row in rows] == ["Correo 0", "Correo 1"]
    assert all(None not in row for row in rows)
    assert all("\n\nPárrafo dos" in row["cuerpo"] for row in rows)


def test_retention_drops_oldest_entries_without_reusing_identifiers():
    state = {}
    for index in range(HISTORY_LIMIT + 2):
        remember_prediction(state, str(index), "Descripción", 100, sample_result())
    assert len(state["prediction_history"]) == HISTORY_LIMIT
    assert state["prediction_history"][0]["id"] == 3
    assert state["prediction_history"][-1]["id"] == HISTORY_LIMIT + 2
    assert state["last_entry"] == state["prediction_history"][-1]
