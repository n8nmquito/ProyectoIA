"""Populate the authored Excel template using only the Python standard library."""

import io
import re
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from app.session_results import export_row, review_reason

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
ET.register_namespace("x", SHEET_NS)
ET.register_namespace("c", CHART_NS)
NS = {"x": SHEET_NS, "c": CHART_NS}
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MISSING = "No registrado"
HISTORY_FIELDS = [
    "id", "fecha_utc", "categoria", "confianza", "requiere_revision",
    "modelo_correos", "titulo", "cuerpo", "p_accesos", "p_aplicaciones",
    "p_infraestructura", "p_otros", "motivo_revision", "umbral_revision",
    "sin_vocabulario", "modelo_archivo", "modelo_sha256", "duracion_ms",
]


def excel_date(value):
    """Store real Excel date serials, normalized to the explicitly labelled UTC."""
    if not value:
        return MISSING
    try:
        date = datetime.fromisoformat(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        date = date.astimezone(timezone.utc).replace(tzinfo=None)
        return (date - datetime(1899, 12, 30)).total_seconds() / 86400
    except (ValueError, TypeError):
        return MISSING


def cell_value(cell, value):
    """Keep typed numbers and write untrusted text as literal inline strings."""
    for child in list(cell):
        cell.remove(child)
    cell.attrib.pop("t", None)
    if value is None or value == "":
        value = MISSING
    if isinstance(value, bool):
        value = "Sí" if value else "No"
    if isinstance(value, (float, int)):
        ET.SubElement(cell, f"{{{SHEET_NS}}}v").text = str(value)
    else:
        cell.set("t", "inlineStr")
        inline = ET.SubElement(cell, f"{{{SHEET_NS}}}is")
        text = ET.SubElement(inline, f"{{{SHEET_NS}}}t")
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        text.text = INVALID_XML.sub("", str(value))


def xlsx_bytes(entries):
    """Produce a styled summary of the latest result and a complete history table."""
    if not entries:
        raise ValueError("No hay predicciones para exportar.")
    source = Path(__file__).parent / "assets/prediction_template.xlsx"
    with zipfile.ZipFile(source) as template:
        parts = {name: template.read(name) for name in template.namelist()}
    entry = entries[-1]
    summary = ET.fromstring(parts["xl/worksheets/sheet1.xml"])
    cells = {cell.get("r"): cell for cell in summary.findall(".//x:c", NS)}
    updates = {
        "B5": entry["categoria"].capitalize(), "E5": entry["confianza"],
        "B7": f"{entry['modelo_correos']} correos", "E7": entry["requiere_revision"],
        "B9": excel_date(entry.get("fecha_utc")), "E9": entry.get("id"),
        "B26": entry["titulo"], "B27": entry["cuerpo"],
        "B30": entry.get("modelo_archivo"), "B31": entry.get("modelo_sha256"),
        "B32": entry.get("umbral_revision"), "E32": entry.get("duracion_ms"),
        "B33": review_reason(entry), "B34": entry.get("sin_vocabulario"),
    }
    probabilities = [entry["probabilidades"][key] for key in
                     ("accesos", "aplicaciones", "infraestructura", "otros")]
    updates.update({f"B{row}": value for row, value in enumerate(probabilities, 12)})
    for address, value in updates.items():
        cell_value(cells[address], value)
    description_row = summary.find(".//x:row[@r='27']", NS)
    lines = sum(max(1, (len(line) + 94) // 95) for line in entry["cuerpo"].splitlines())
    description_row.set("ht", str(min(409, max(100, lines * 15 + 15))))
    description_row.set("customHeight", "1")
    parts["xl/worksheets/sheet1.xml"] = ET.tostring(summary, encoding="utf-8", xml_declaration=True)

    history = ET.fromstring(parts["xl/worksheets/sheet2.xml"])
    data = history.find("x:sheetData", NS)
    seed = data.find("x:row[@r='6']", NS)
    if seed is None:
        raise ValueError("La plantilla Excel no contiene la fila de datos.")
    seed = deepcopy(seed)
    for row in list(data):
        if int(row.get("r")) >= 6:
            data.remove(row)
    for row_index, record in enumerate(entries, 6):
        row = deepcopy(seed)
        row.set("r", str(row_index))
        values = export_row(record)
        for column, cell in enumerate(row.findall("x:c", NS)):
            address = cell.get("r")
            cell.set("r", re.sub(r"\d+$", str(row_index), address))
            value = values[HISTORY_FIELDS[column]]
            if HISTORY_FIELDS[column] == "fecha_utc":
                value = excel_date(value)
            elif HISTORY_FIELDS[column] == "categoria":
                value = value.capitalize()
            cell_value(cell, value)
        lines = sum(max(1, (len(line) + 79) // 80)
                    for line in record["cuerpo"].splitlines())
        row.set("ht", str(min(409, max(65, (lines + 2) * 15))))
        row.set("customHeight", "1")
        data.append(row)
    last = 5 + len(entries)
    dimension = history.find("x:dimension", NS)
    if dimension is not None:
        dimension.set("ref", f"A1:R{last}")
    parts["xl/worksheets/sheet2.xml"] = ET.tostring(history, encoding="utf-8", xml_declaration=True)
    table = ET.fromstring(parts["xl/tables/table1.xml"])
    table.set("ref", f"A5:R{last}")
    auto_filter = table.find("x:autoFilter", NS)
    if auto_filter is None:
        auto_filter = ET.Element(f"{{{SHEET_NS}}}autoFilter")
        table.insert(0, auto_filter)
    auto_filter.set("ref", f"A5:R{last}")
    parts["xl/tables/table1.xml"] = ET.tostring(table, encoding="utf-8", xml_declaration=True)
    for name in list(parts):
        if "/charts/" in name and name.endswith(".xml"):
            chart = ET.fromstring(parts[name])
            for cache in chart.findall(".//c:numCache", NS):
                for child in list(cache):
                    if child.tag != f"{{{CHART_NS}}}formatCode":
                        cache.remove(child)
                ET.SubElement(cache, f"{{{CHART_NS}}}ptCount", val="4")
                for index, value in enumerate(probabilities):
                    point = ET.SubElement(cache, f"{{{CHART_NS}}}pt", idx=str(index))
                    ET.SubElement(point, f"{{{CHART_NS}}}v").text = str(value)
            for cache in chart.findall(".//c:strCache", NS):
                cache.clear()
                ET.SubElement(cache, f"{{{CHART_NS}}}ptCount", val="4")
                for index, label in enumerate(("Accesos", "Aplicaciones", "Infraestructura", "Otros")):
                    point = ET.SubElement(cache, f"{{{CHART_NS}}}pt", idx=str(index))
                    ET.SubElement(point, f"{{{CHART_NS}}}v").text = label
            parts[name] = ET.tostring(chart, encoding="utf-8", xml_declaration=True)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as workbook:
        for name, content in parts.items():
            # Stable bytes keep Streamlit's download URL valid across rerenders.
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            workbook.writestr(info, content)
    return output.getvalue()
