"""Validated loading and deterministic cleaning of Spanish tickets."""

import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

CLASSES = ("accesos", "aplicaciones", "infraestructura", "otros")
MAX_LENGTH = 20000


def clean_text(value):
    """Normalize text, remove contact identifiers and attachment names."""
    if not isinstance(value, str):
        raise ValueError("El título y el cuerpo deben ser cadenas de texto.")
    text = unicodedata.normalize("NFKC", html.unescape(value)).lower()
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " enlace ", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", " correo ", text)
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", " direccion ", text)
    text = re.sub(
        r"\b[\w.-]+\.(?:txt|log|json|xml|pdf|png|jpg)\b", " adjunto ", text
    )
    text = re.sub(r"\b\d{5,}\b", " numero ", text)
    text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
    return " ".join(text.split())


def combine_text(title, body):
    """Validate and combine title and body."""
    for name, value in (("título", title), ("cuerpo", body)):
        if not isinstance(value, str):
            raise ValueError(f"El {name} debe ser texto.")
        if len(value) > MAX_LENGTH:
            raise ValueError(
                f"El {name} supera el máximo de {MAX_LENGTH} caracteres."
            )
        if not any(char.isalpha() for char in clean_text(value)):
            raise ValueError(
                f"Escribe un {name} con letras; no solo símbolos o números."
            )
    return clean_text(f"{title} {body}")


def load_data(path):
    """Load, validate and deduplicate a JSON list of tickets."""
    source = Path(path)
    try:
        records = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo cargar {source}: {exc}") from exc
    if not isinstance(records, list) or not records:
        raise ValueError(
            "correos.json debe contener una lista no vacía de objetos."
        )
    if not all(isinstance(row, dict) for row in records):
        raise ValueError("Cada correo debe ser un objeto JSON.")
    frame = pd.DataFrame(records)
    required = {"titulo", "cuerpo", "clasificacion"}
    if not required.issubset(frame.columns):
        raise ValueError(
            f"Faltan columnas: {sorted(required - set(frame.columns))}"
        )
    if frame[list(required)].isna().any().any():
        raise ValueError(
            "Hay títulos, cuerpos o etiquetas faltantes; revisar el origen."
        )
    if not frame["clasificacion"].isin(CLASSES).all():
        raise ValueError(
            f"Las etiquetas permitidas son: {', '.join(CLASSES)}."
        )
    frame = frame[list(sorted(required))].copy()
    texts = []
    for index, row in frame.iterrows():
        try:
            texts.append(combine_text(row["titulo"], row["cuerpo"]))
        except ValueError as exc:
            raise ValueError(f"Registro {index}: {exc}") from exc
    frame["texto"] = texts
    conflicts = frame.groupby("texto")["clasificacion"].nunique()
    if (conflicts > 1).any():
        raise ValueError(
            "Existen tickets idénticos con etiquetas contradictorias."
        )
    frame = frame.drop_duplicates("texto").reset_index(drop=True)
    if set(frame["clasificacion"]) != set(CLASSES):
        raise ValueError("El dataset debe representar las cuatro clases.")
    return frame


def ticket_fingerprint(text):
    """Identify a normalized ticket without relying on its row position."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_from_manifest(frame, manifest_path, cv_folds):
    """Keep a recorded holdout unchanged when training data is extended."""
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        entries = manifest["test_tickets"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("No se pudo leer el test reservado.") from exc
    if not isinstance(entries, list) or not entries:
        raise ValueError("El manifiesto debe reservar al menos un ticket.")
    if not all(
        isinstance(entry, dict)
        and isinstance(entry.get("fingerprint"), str)
        and entry.get("clasificacion") in CLASSES
        for entry in entries
    ):
        raise ValueError("El manifiesto contiene tickets inválidos.")
    fingerprints = [entry["fingerprint"] for entry in entries]
    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError(
            "El test reservado contiene identificadores repetidos."
        )
    lookup = dict(zip(frame.texto.map(ticket_fingerprint), frame.index))
    if set(fingerprints) - set(lookup):
        raise ValueError("Faltan tickets del test reservado; no se redibuja.")
    test = frame.loc[[lookup[value] for value in fingerprints]].copy()
    expected = [entry["clasificacion"] for entry in entries]
    if test.clasificacion.tolist() != expected:
        raise ValueError(
            "Las etiquetas del test reservado fueron modificadas."
        )
    train = frame.drop(index=test.index).copy()
    if set(test.clasificacion) != set(CLASSES):
        raise ValueError("El test reservado debe incluir las cuatro clases.")
    if (
        set(train.clasificacion) != set(CLASSES)
        or train.clasificacion.value_counts().min() < cv_folds
    ):
        raise ValueError("Train no tiene suficientes tickets por clase.")
    return train, test


def split_data(
    frame, test_size=0.2, seed=42, cv_folds=4, holdout_manifest=None
):
    """Create stratified partitions and check training counts for CV."""
    if holdout_manifest is not None:
        return split_from_manifest(frame, holdout_manifest, cv_folds)
    try:
        train, test = train_test_split(
            frame,
            test_size=test_size,
            random_state=seed,
            stratify=frame["clasificacion"],
        )
    except ValueError as exc:
        raise ValueError(
            f"No hay suficientes datos para dividir por clase: {exc}"
        ) from exc
    if set(test["clasificacion"]) != set(CLASSES):
        raise ValueError(
            "El conjunto de prueba debe incluir las cuatro clases."
        )
    if train["clasificacion"].value_counts().min() < cv_folds:
        raise ValueError(
            "No hay suficientes tickets por clase para los folds solicitados."
        )
    return train.copy(), test.copy()
