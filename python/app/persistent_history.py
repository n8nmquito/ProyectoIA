"""Persistent histories isolated by random, private link identifiers."""

import hashlib
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{32,64}\Z")


def history_token(value=None):
    """Keep valid link identifiers or generate an unguessable new identifier."""
    if isinstance(value, str) and TOKEN_PATTERN.fullmatch(value):
        return value
    return secrets.token_urlsafe(24)


class HistoryStore:
    """Use transactions to append, prune and clear one link's saved history."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS histories "
                "(owner TEXT NOT NULL, sequence INTEGER NOT NULL, "
                "payload TEXT NOT NULL, PRIMARY KEY (owner, sequence))"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS sequences "
                "(owner TEXT PRIMARY KEY, value INTEGER NOT NULL)"
            )

    @contextmanager
    def connect(self):
        """Open a short-lived connection; never share connections across sessions."""
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def owner(token):
        """Validate the private identifier and keep only its hash in the database."""
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            raise ValueError("Invalid history identifier")
        return hashlib.sha256(token.encode()).hexdigest()

    def load(self, token):
        """Read only the records belonging to the supplied private link."""
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM histories WHERE owner=? ORDER BY sequence",
                (self.owner(token),),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def append(self, token, entry, limit=50):
        """Append once, allocate a unique ID and retain the latest records atomically."""
        owner = self.owner(token)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT OR IGNORE INTO sequences(owner, value) VALUES (?, 0)",
                (owner,),
            )
            connection.execute(
                "UPDATE sequences SET value=value+1 WHERE owner=?", (owner,)
            )
            sequence = connection.execute(
                "SELECT value FROM sequences WHERE owner=?", (owner,)
            ).fetchone()[0]
            saved = {**entry, "id": sequence}
            connection.execute(
                "INSERT INTO histories(owner, sequence, payload) VALUES (?, ?, ?)",
                (owner, sequence, json.dumps(saved, ensure_ascii=False)),
            )
            connection.execute(
                "DELETE FROM histories WHERE owner=? AND sequence NOT IN "
                "(SELECT sequence FROM histories WHERE owner=? "
                "ORDER BY sequence DESC LIMIT ?)",
                (owner, owner, limit),
            )
        return saved

    def clear(self, token):
        """Clear this history without deleting another link's records or its counter."""
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM histories WHERE owner=?", (self.owner(token),)
            )


def configured_store():
    """Enable persistence only when the deployment supplies a writable path."""
    path = os.environ.get("HISTORY_DB_PATH")
    return HistoryStore(path) if path else None
