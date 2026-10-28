"""Check privacy transformations without losing the reported support issue."""

import pytest

from src.email_privacy import sanitize_ticket


@pytest.mark.parametrize("signature", [
    "-- \nMaría Prueba\nTel: +506 8888-9999",
    "Saludos cordiales,\nMaría Prueba\nmaria@example.test",
    "Enviado desde mi iPhone",
    "Best regards,\nTest Person\nprivate@example.test",
    "AVISO DE CONFIDENCIALIDAD\nEste mensaje es confidencial.",
])
def test_removes_common_trailing_signatures(signature):
    result = sanitize_ticket("Error JDE", "No guarda la orden en JDE.\n\n" + signature)
    assert result["cuerpo"] == "No guarda la orden en JDE."
    assert result["limpieza"]["firma_eliminada"]


def test_html_signature_and_scripts_are_not_forwarded():
    result = sanitize_ticket("Error JDE", '<p>No guarda la orden.</p>'
        '<script>secretScript</script><div class="gmail_signature">'
        '<p>María Prueba<br>maria@example.test</p></div>')
    assert "No guarda la orden." in result["cuerpo"]
    assert "María" not in result["cuerpo"]
    assert "secretScript" not in result["cuerpo"]
    assert "example.test" not in result["cuerpo"]
    assert result["limpieza"]["firma_eliminada"]


def test_redacts_identifiers_and_credentials_in_both_fields():
    result = sanitize_ticket("Acceso de maria@example.test", "\n".join([
        "No puedo ingresar a JDE desde 192.168.10.20 o 2001:db8::1.",
        "Mi contacto es +506 8888-9999.",
        "Cédula: 1-2345-6789; usuario: mprueba",
        "Nombre completo: María Prueba",
        "Dirección postal: Calle de Prueba 123",
        "password: secreto123; token=abc123; Authorization: Bearer token-demo",
        "Pruebo https://example.test/login?password=secreto",
        "Tarjeta 4111 1111 1111 1111",
    ]))
    text = result["titulo"] + result["cuerpo"]
    for private in ["maria@example", "192.168.10.20", "2001:db8::1", "8888",
                    "2345", "mprueba", "María Prueba", "Calle de Prueba",
                    "secreto123", "abc123", "token-demo", "password=secreto",
                    "4111"]:
        assert private not in text
    assert "JDE" in text
    assert result["limpieza"]["datos_redactados"]["correo"] == 1
    assert result["limpieza"]["datos_redactados"]["ip"] == 2


def test_preserves_meaning_dates_versions_and_normal_sentences():
    body = "Atentamente solicito revisar JDE 9.2 desde 2026-10-28.\nError al guardar una orden; mis compañeros pueden acceder."
    result = sanitize_ticket("Error al guardar", body)
    assert result["cuerpo"] == body
    assert not result["limpieza"]["firma_eliminada"]


def test_empty_cleaned_body_has_an_informative_error():
    with pytest.raises(ValueError, match="No quedó"):
        sanitize_ticket("Error JDE", '<div class="gmail_signature">Firma</div>')
