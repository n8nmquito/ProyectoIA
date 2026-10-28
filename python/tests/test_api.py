"""Check authentication, validation and parity with the real saved pipeline."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.model import predict_ticket

ROOT = Path(__file__).resolve().parents[1]
TEST_KEY = "synthetic-test-only-" + "x" * 32


@pytest.fixture()
def client():
    """Start the real model using a synthetic in-memory API key."""
    with TestClient(create_app(api_key=TEST_KEY)) as test_client:
        yield test_client


def test_authentication(client):
    """Reject unauthenticated callers."""
    response = client.post("/predict", json={
        "titulo": "Error de acceso", "cuerpo": "No puedo entrar al sistema"
    })
    assert response.status_code == 401


@pytest.mark.parametrize("payload", [
    {"titulo": "!!!", "cuerpo": "???"},
    {"titulo": "Error", "cuerpo": ""},
    {"titulo": 123, "cuerpo": "texto"},
    {"titulo": "Error", "cuerpo": "texto", "remitente": "privado"},
])
def test_invalid_input(client, payload):
    """Reject empty, symbolic, incorrectly typed or additional fields."""
    response = client.post(
        "/predict", json=payload, headers={"X-API-Key": TEST_KEY}
    )
    assert response.status_code == 422
    assert "privado" not in response.text


def test_predictions_match_all_25_emails(client):
    """Require HTTP predictions to match direct Python inference exactly."""
    records = json.loads((ROOT / "data/test/correos_test_25.json").read_text(
        encoding="utf-8-sig"
    ))
    assert len(records) == 25
    for record in records:
        expected = predict_ticket(
            client.app.state.pipeline, record["titulo"], record["cuerpo"]
        )
        response = client.post("/predict", json={
            "titulo": record["titulo"], "cuerpo": record["cuerpo"]
        }, headers={"X-API-Key": TEST_KEY})
        assert response.status_code == 200
        actual = response.json()
        for key in expected:
            assert actual[key] == expected[key]
        assert actual["muestras_entrenamiento"] == 300
        assert abs(sum(actual["probabilidades"].values()) - 1) < 1e-9


def test_refuses_smaller_model():
    """Prevent deployment of a different training version by mistake."""
    with pytest.raises(RuntimeError, match="300 correos"):
        with TestClient(create_app(
            model_path=ROOT / "models/modelo_clasificador_100.pkl",
            api_key=TEST_KEY,
        )):
            pass


def test_requires_key():
    """Fail startup if no sufficiently long key is configured."""
    with pytest.raises(RuntimeError, match="CLASSIFIER_API_KEY"):
        with TestClient(create_app(api_key="")):
            pass


def test_no_sanitization_endpoint(client):
    """Keep email cleaning inside n8n, outside the classification API."""
    assert client.post("/sanitize", json={}).status_code == 404
