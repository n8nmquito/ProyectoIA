"""Configuration, serialization and artifact paths."""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


def load_config(path=None):
    """Load and validate the YAML configuration relative to the project."""
    source = project_path(path) if path else ROOT / "config.yaml"
    try:
        config = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(
            f"No se pudo leer la configuración {source}: {exc}"
        ) from exc
    if not isinstance(config, dict):
        raise ValueError("La configuración debe ser un objeto YAML.")
    if path:
        defaults = load_config()
        for section in ("model", "tfidf"):
            if section in config and isinstance(config[section], dict):
                config[section] = defaults[section] | config[section]
        config = defaults | config
    if "HISTORY_LIMIT" in os.environ:
        try:
            config["history_limit"] = int(os.environ["HISTORY_LIMIT"])
        except ValueError as exc:
            raise ValueError(
                "HISTORY_LIMIT debe ser un entero positivo."
            ) from exc
    validate_settings(config)
    if not 0 < config.get("test_size", 0) < 1:
        raise ValueError("test_size debe estar entre 0 y 1.")
    if config.get("cv_folds", 0) < 2:
        raise ValueError("cv_folds debe ser al menos 2.")
    if not 0 <= config.get("confidence_threshold", -1) <= 1:
        raise ValueError("confidence_threshold debe estar entre 0 y 1.")
    return config


def validate_settings(config):
    """Validate configurable history, text features and model settings."""
    limit = config.get("history_limit")
    if type(limit) is not int or limit < 1:
        raise ValueError("history_limit debe ser un entero positivo.")
    model = config.get("model")
    tfidf = config.get("tfidf")
    if not isinstance(model, dict) or not isinstance(tfidf, dict):
        raise ValueError("model y tfidf deben ser objetos YAML.")
    for field, minimum in (("logistic_max_iter", 1), ("calibration_folds", 2)):
        value = model.get(field)
        if type(value) is not int or value < minimum:
            raise ValueError(f"model.{field} debe ser un entero >= {minimum}.")
    ngrams = tfidf.get("ngram_range")
    if (
        not isinstance(ngrams, (list, tuple))
        or len(ngrams) != 2
        or any(type(value) is not int for value in ngrams)
        or not 1 <= ngrams[0] <= ngrams[1]
    ):
        raise ValueError(
            "tfidf.ngram_range debe ser [mínimo, máximo] válidos."
        )
    if type(tfidf.get("sublinear_tf")) is not bool:
        raise ValueError("tfidf.sublinear_tf debe ser true o false.")
    if tfidf.get("strip_accents") not in (None, "ascii", "unicode"):
        raise ValueError("tfidf.strip_accents debe ser null, ascii o unicode.")


def history_limit():
    """Read the retention limit with its environment override."""
    return load_config()["history_limit"]


def project_path(value):
    """Resolve a configurable path using the project as base."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def save_json(path, value):
    """Write JSON with readable accents and informative I/O errors."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except OSError as exc:
        raise OSError(f"No se pudo guardar {path}: {exc}") from exc


def file_hash(path):
    """Return the SHA-256 fingerprint of an input or model file."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as exc:
        raise OSError(f"No se pudo verificar {path}: {exc}") from exc


def save_csv(frame, path, **kwargs):
    """Export CSV, retaining an open Windows file and reporting a new path."""
    path = Path(path)
    try:
        frame.to_csv(path, **kwargs)
        return path
    except PermissionError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        alternate = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
        try:
            frame.to_csv(alternate, **kwargs)
        except OSError as exc:
            raise OSError(
                f"No se pudo guardar {path} ni una copia alternativa: {exc}"
            ) from exc
        LOGGER.warning("CSV bloqueado: %s. Actualizado: %s", path, alternate)
        return alternate
