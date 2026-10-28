"""Session-only prediction history and spreadsheet-safe CSV downloads."""

import csv
import io
from copy import deepcopy
from datetime import datetime, timezone

HISTORY_LIMIT = 50


def remember_prediction(state, title, body, size, result, store=None, token=None):
    """Keep an independent snapshot of each successful explicit prediction."""
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
        entry = store.append(token, entry, HISTORY_LIMIT)
    state["prediction_sequence"] = entry["id"]
    state["prediction_history"] = (
        state.get("prediction_history", []) + [entry]
    )[-HISTORY_LIMIT:]
    state["last_entry"] = entry
    state.pop("comparison_ids", None)


def csv_bytes(entries):
    """Export actual predictions as UTF-8 CSV, neutralizing cell formulas."""
    columns = [
        "id", "fecha_utc", "modelo_correos", "titulo", "cuerpo",
        "categoria", "confianza", "requiere_revision",
        "p_accesos", "p_aplicaciones", "p_infraestructura", "p_otros",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for entry in entries:
        row = {key: entry.get(key, "") for key in columns}
        for category, value in entry["probabilidades"].items():
            row[f"p_{category}"] = value
        for key in ("titulo", "cuerpo"):
            value = str(row[key])
            if value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            row[key] = value
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")
