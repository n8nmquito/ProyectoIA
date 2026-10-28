"""Session-only prediction history and spreadsheet-safe CSV downloads."""

import csv
import io
from copy import deepcopy
from datetime import datetime, timezone

from src.utils import history_limit

CSV_COLUMNS = [
    "id",
    "fecha_utc",
    "modelo_correos",
    "titulo",
    "cuerpo",
    "categoria",
    "confianza",
    "requiere_revision",
    "p_accesos",
    "p_aplicaciones",
    "p_infraestructura",
    "p_otros",
    "sin_vocabulario",
    "umbral_revision",
    "modelo_archivo",
    "modelo_sha256",
    "duracion_ms",
    "motivo_revision",
]


def review_reason(entry):
    """Describe review signals using only recorded thresholds."""
    if entry.get("sin_vocabulario"):
        return "El texto no contiene términos del vocabulario del modelo."
    if entry.get("requiere_revision"):
        threshold = entry.get("umbral_revision")
        if threshold is not None and entry["confianza"] < threshold:
            return (
                f"Confianza inferior al umbral de revisión ({threshold:.0%})."
            )
        return "Revisión indicada por el modelo; consultar el caso."
    return "No se activó una alerta automática de revisión."


def export_row(entry):
    """Expose the same recorded data to CSV and formatted Excel exports."""
    row = {key: entry.get(key, "") for key in CSV_COLUMNS}
    for category, value in entry["probabilidades"].items():
        row[f"p_{category}"] = value
    row["motivo_revision"] = review_reason(entry)
    return row


def remember_prediction(
    state, title, body, size, result, store=None, token=None
):
    """Keep an independent snapshot of each successful explicit prediction."""
    limit = history_limit()
    sequence = state.get("prediction_sequence", 0) + 1
    entry = {
        "id": sequence,
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo_correos": size,
        "titulo": title,
        "cuerpo": body,
        **deepcopy(result),
    }
    if store is not None:
        entry = store.append(token, entry, limit)
    state["prediction_sequence"] = entry["id"]
    state["prediction_history"] = (
        state.get("prediction_history", []) + [entry]
    )[-limit:]
    state["last_entry"] = entry
    state.pop("comparison_ids", None)


def csv_bytes(entries):
    """Export UTF-8 CSV with an explicit Excel separator directive."""
    output = io.StringIO(newline="")
    # Excel uses the regional list separator unless the file declares one.
    output.write("sep=;\r\n")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        delimiter=";",
        quoting=csv.QUOTE_ALL,
        lineterminator="\r\n",
    )
    writer.writeheader()
    for entry in entries:
        row = export_row(entry)
        for key in ("titulo", "cuerpo"):
            value = str(row[key])
            if value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            row[key] = value
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")
