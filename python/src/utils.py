"""Configuration, serialization and artifact paths."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


def load_config(path=None):
    """Load and validate the YAML configuration relative to the project."""
    source = Path(path) if path else ROOT / "config.yaml"
    try:
        config = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(
            f"No se pudo leer la configuración {source}: {exc}"
        ) from exc
    if not isinstance(config, dict):
        raise ValueError("La configuración debe ser un objeto YAML.")
    if not 0 < config.get("test_size", 0) < 1:
        raise ValueError("test_size debe estar entre 0 y 1.")
    if config.get("cv_folds", 0) < 2:
        raise ValueError("cv_folds debe ser al menos 2.")
    if not 0 <= config.get("confidence_threshold", -1) <= 1:
        raise ValueError("confidence_threshold debe estar entre 0 y 1.")
    return config


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
