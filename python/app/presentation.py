"""Presentation helpers for the local Streamlit interface."""

from pathlib import Path

import streamlit as st

ICONS = {
    "ticket": '<path d="M5 3h14a2 2 0 0 1 2 2v3a3 3 0 0 0 0 6v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5a3 3 0 0 0 0-6V5a2 2 0 0 1 2-2Z"/><path d="M10 8h4m-2 0v8m-2 0h4"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 12h8M8 16h6"/>',
    "chart": '<path d="M4 20V12m5 8V4m6 16v-9m5 9V8"/>',
    "spark": '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
    "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
    "tag": '<path d="M20 13 11 22 2 13V3h10l8 9a1 1 0 0 1 0 1Z"/><circle cx="7" cy="8" r="1"/>',
}


def icon(name):
    """Return a decorative inline icon from the fixed local collection."""
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">'
        + ICONS[name] + '</svg>'
    )


def apply_style(theme="dark"):
    """Apply per-session styling without changing other users' settings."""
    css = (Path(__file__).parent / "assets/style.css").read_text(
        encoding="utf-8"
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    if theme == "light":
        light_css = (Path(__file__).parent / "assets/light.css").read_text(
            encoding="utf-8"
        )
        st.markdown(f"<style>{light_css}</style>", unsafe_allow_html=True)


def heading(label, name):
    """Render a section heading using fixed application text."""
    st.markdown(
        f'<h2 class="panel-heading">{icon(name)}<span>{label}</span></h2>',
        unsafe_allow_html=True,
    )


def empty_result(language="Español"):
    """Explain the next action and expected outputs with decorative SVG icons."""
    english = language == "English"
    title = "Ready to classify" if english else "Listo para clasificar"
    description = (
        "Enter a title and description. Your suggested category and confidence "
        "will appear here." if english else
        "Escribe el título y la descripción del ticket. Aquí verás la categoría "
        "sugerida y la confianza del modelo."
    )
    labels = (("tag", "Category" if english else "Categoría"),
              ("shield", "Confidence" if english else "Confianza"),
              ("chart", "Probabilities" if english else "Probabilidades"))
    features = "".join(
        f'<div class="empty-feature">{icon(name)}<span>{label}</span></div>'
        for name, label in labels
    )
    tip = (
        'Not sure where to start? Select <strong>Try an example</strong>.'
        if english else
        '¿No sabes por dónde empezar? Pulsa <strong>Prueba con ejemplo</strong>.'
    )
    st.markdown(
        '<div class="empty-result"><div class="empty-illustration">'
        '<div class="empty-icon">'
        + icon("document")
        + '</div><span class="empty-spark">' + icon("spark")
        + '</span></div>'
        + f'<p class="empty-title" role="heading" aria-level="3">{title}</p>'
        + f'<p class="empty-description">{description}</p>'
        + f'<div class="empty-features">{features}</div>'
        + f'<p class="empty-tip">{tip}</p></div>',
        unsafe_allow_html=True,
    )
