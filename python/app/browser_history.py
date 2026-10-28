"""Keep the private history identifier in this browser, without external services."""

from pathlib import Path

import streamlit.components.v1 as components

from app.persistent_history import TOKEN_PATTERN

_identity = components.declare_component(
    "history_identity", path=str(Path(__file__).parent / "history_component")
)


def browser_history_token(link_token=None):
    """Restore a browser's history or adopt an explicitly supplied private link."""
    valid = (link_token if isinstance(link_token, str)
             and TOKEN_PATTERN.fullmatch(link_token) else None)
    return _identity(link_token=valid, default=valid, key="history_identity")
