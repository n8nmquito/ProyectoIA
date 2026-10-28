"""Verify typed values, complete metadata and safe formatted Excel reports."""

import io
import zipfile
from xml.etree import ElementTree as ET

from app.excel_export import NS, xlsx_bytes
from app.session_results import remember_prediction


def entry(metadata=True):
    result = {
        "categoria": "accesos", "confianza": .55, "requiere_revision": True,
        "sin_vocabulario": False,
        "probabilidades": {"accesos": .55, "aplicaciones": .2,
                           "infraestructura": .15, "otros": .1},
    }
    if metadata:
        result.update(umbral_revision=.6, modelo_archivo="modelo_clasificador_300.pkl",
                      modelo_sha256="a" * 64, duracion_ms=0)
    state = {}
    remember_prediction(state, '=HYPERLINK("texto")',
                        'Descripción; "comillas"\nSegundo párrafo', 300, result)
    return state["last_entry"]


def read_cell(sheet, address):
    cell = sheet.find(f".//x:c[@r='{address}']", NS)
    if cell.get("t") == "inlineStr":
        return cell.find("x:is/x:t", NS).text
    return float(cell.find("x:v", NS).text)


def test_excel_keeps_real_probabilities_metadata_and_literal_user_text():
    record = entry()
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes([record, record]))) as book:
        summary = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        history = ET.fromstring(book.read("xl/worksheets/sheet2.xml"))
        assert read_cell(summary, "B5") == "Accesos"
        assert read_cell(summary, "E5") == .55
        assert read_cell(summary, "B12") == .55
        assert read_cell(summary, "B32") == .6
        assert read_cell(summary, "E32") == 0
        assert read_cell(summary, "B31") == "a" * 64
        assert read_cell(summary, "B26") == record["titulo"]
        assert read_cell(summary, "B27") == record["cuerpo"]
        assert "60%" in read_cell(summary, "B33")
        assert not summary.findall(".//x:f", NS)
        assert not history.findall(".//x:f", NS)
        assert read_cell(history, "D6") == .55
        assert read_cell(history, "B6") > 40000
        assert read_cell(history, "G7") == record["titulo"]
        table = ET.fromstring(book.read("xl/tables/table1.xml"))
        assert table.get("ref") == "A5:R7"
        chart = ET.fromstring(book.read("xl/drawings/charts/chart1.xml"))
        values = [float(value.text) for value in chart.findall(".//c:numCache/c:pt/c:v", NS)]
        assert values == [.55, .2, .15, .1]


def test_historical_report_does_not_invent_missing_model_metadata():
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes([entry(metadata=False)]))) as book:
        summary = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        for address in ("B30", "B31", "B32", "E32"):
            assert read_cell(summary, address) == "No registrado"
        assert "60%" not in read_cell(summary, "B33")


def test_download_bytes_do_not_change_when_the_clock_advances(monkeypatch):
    record = entry()
    monkeypatch.setattr("zipfile.time.localtime", lambda *_: (2020, 1, 1, 0, 0, 0, 0, 1, 0))
    first = xlsx_bytes([record])
    monkeypatch.setattr("zipfile.time.localtime", lambda *_: (2030, 1, 1, 0, 0, 0, 0, 1, 0))
    assert xlsx_bytes([record]) == first
