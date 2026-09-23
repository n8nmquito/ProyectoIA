#!/usr/bin/env python3
"""Genera claves internas y el hash de n8n sin publicar secretos en Git."""
import os
from pathlib import Path
import re
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent


def read_env(path):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not re.fullmatch(r"[A-Z0-9_]+", key.strip()):
            raise ValueError(f"Formato incorrecto en {path.name}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def save_env(path, values):
    temporary = path.with_suffix(".tmp")
    temporary.write_text("".join(f"{key}='{value}'\n" for key, value in values.items()), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def main():
    env = read_env(ROOT / ".env")
    required = ("ADMIN_EMAIL", "ADMIN_PASSWORD", "POSTGRES_PASSWORD",
                "N8N_DB_PASSWORD", "REDMINE_DB_PASSWORD")
    for key in required:
        if not env.get(key):
            raise ValueError(f"Completar {key} en .env")
    if env.get("POSTGRES_USER", "postgres") in ("n8n", "redmine"):
        raise ValueError("POSTGRES_USER debe ser distinto de n8n y redmine")
    password = env["ADMIN_PASSWORD"]
    if len(password.encode("utf-8")) > 72:
        raise ValueError("ADMIN_PASSWORD debe ocupar como máximo 72 bytes para bcrypt")
    result = subprocess.run(
        ["docker", "run", "--rm", "-i", "httpd:2.4-alpine",
         "htpasswd", "-niBC", "12", "admin"],
        input=password + "\n", text=True, capture_output=True,
    )
    if result.returncode:
        raise RuntimeError("No se pudo generar bcrypt. Verificar Docker y acceso a httpd:2.4-alpine.")
    hashed = result.stdout.strip().partition(":")[2]
    if not re.fullmatch(r"\$2[aby]\$12\$[./A-Za-z0-9]{53}", hashed):
        raise RuntimeError("El generador devolvió un hash no válido")
    folder = ROOT / ".secrets"
    folder.mkdir(mode=0o700, exist_ok=True)
    n8n = read_env(folder / "n8n.env")
    redmine = read_env(folder / "redmine.env")
    # Conservar claves existentes, incluso al migrar el formato anterior.
    n8n["N8N_ENCRYPTION_KEY"] = n8n.get("N8N_ENCRYPTION_KEY") or env.get("N8N_ENCRYPTION_KEY") or secrets.token_hex(32)
    n8n["N8N_INSTANCE_OWNER_PASSWORD_HASH"] = hashed
    redmine["SECRET_KEY_BASE"] = redmine.get("SECRET_KEY_BASE") or env.get("REDMINE_SECRET_KEY_BASE") or secrets.token_hex(32)
    save_env(folder / "n8n.env", n8n)
    save_env(folder / "redmine.env", redmine)
    print("Configuración interna preparada. Las claves existentes se conservaron.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error)) from None
