"""Presentation helpers for the local Streamlit interface."""

from pathlib import Path

import streamlit as st

ICONS = {
    "ticket": '<path d="M5 3h14a2 2 0 0 1 2 2v3a3 3 0 0 0 0 6v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5a3 3 0 0 0 0-6V5a2 2 0 0 1 2-2Z"/><path d="M10 8h4m-2 0v8m-2 0h4"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 12h8M8 16h6"/>',
    "chart": '<path d="M4 20V12m5 8V4m6 16v-9m5 9V8"/>',
}


def icon(name):
    """Return a decorative inline icon from the fixed local collection."""
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">'
        + ICONS[name] + '</svg>'
    )


def apply_style():
    """Load the local stylesheet without external fonts or network calls."""
    css = (Path(__file__).parent / "assets/style.css").read_text(
        encoding="utf-8"
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def heading(label, name):
    """Render a section heading using fixed application text."""
    st.markdown(
        f'<h2 class="panel-heading">{icon(name)}<span>{label}</span></h2>',
        unsafe_allow_html=True,
    )


def empty_result():
    """Show the centered placeholder until a ticket is classified."""
    st.markdown(
        '<div class="empty-result"><div class="empty-icon">'
        + icon("document")
        + '</div><strong>Sin resultados.</strong>'
        '<p>Completa los campos y pulsa<br>Clasificar.</p></div>',
        unsafe_allow_html=True,
    )
