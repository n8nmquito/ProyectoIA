"""Remove email signatures and sensitive text before inference."""

import ipaddress
import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser

SIGNOFF = re.compile(
    r"^(?:saludos(?: cordiales)?|cordialmente|atentamente|un saludo|"
    r"gracias y saludos|best regards|kind regards|regards|sincerely)[,.!\s]*$",
    re.IGNORECASE,
)
FOOTER = re.compile(
    r"^(?:aviso de confidencialidad|confidentiality notice|"
    r"este (?:mensaje|correo).{0,100}confidencial|"
    r"this (?:message|e-?mail).{0,100}confidential)",
    re.IGNORECASE,
)


class EmailText(HTMLParser):
    """Extract text while excluding scripts, styles and marked signatures."""

    def __init__(self):
        """Initialize extracted text and the stack of excluded elements."""
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = []
        self.signature_removed = False

    def handle_starttag(self, tag, attrs):
        """Retain line boundaries and suppress known signature containers."""
        attributes = dict(attrs)
        marker = " ".join(
            str(attributes.get(key, "")) for key in ("class", "id")
        ).lower()
        signature = any(
            value in marker
            for value in ("gmail_signature", "moz-signature", "signature")
        )
        hidden = self.hidden or tag in ("script", "style") or signature
        if signature:
            self.signature_removed = True
        if hidden:
            if tag not in ("br", "img", "hr", "input", "meta", "link"):
                self.hidden.append(tag)
        elif tag in ("br", "p", "div", "li", "tr", "hr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        """End excluded containers without leaking nested signature text."""
        if self.hidden:
            if tag in self.hidden:
                while self.hidden.pop() != tag:
                    pass
        elif tag in ("p", "div", "li", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        """Collect only visible content outside excluded containers."""
        if not self.hidden:
            self.parts.append(data)


def plain_email(text):
    """Convert email HTML to text and remove complete signature blocks."""
    if not isinstance(text, str):
        raise ValueError("El título y el cuerpo deben ser texto.")
    removed = False
    if re.search(r"</?[a-z][^>]*>", text, re.IGNORECASE):
        parser = EmailText()
        parser.feed(text)
        text = "".join(parser.parts)
        removed = parser.signature_removed
    return unescape(text).replace("\r\n", "\n").replace("\r", "\n"), removed


def remove_signature(text):
    """Cut common trailing signoffs, RFC delimiters and mobile signatures."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        trimmed = line.strip()
        has_content = any(previous.strip() for previous in lines[:index])
        delimiter = trimmed == "--"
        mobile = re.match(
            r"^(?:enviado desde|sent from my)\b", trimmed, re.IGNORECASE
        )
        signoff = SIGNOFF.fullmatch(trimmed) and len(lines) - index <= 15
        if has_content and (
            delimiter or mobile or signoff or FOOTER.match(trimmed)
        ):
            return "\n".join(lines[:index]).strip(), True
    return text.strip(), False


def redact_sensitive(text, counts):
    """Redact common identifiers and secrets without returning their values."""

    def replace(pattern, label, flags=0):
        nonlocal text
        text, count = re.subn(pattern, f"[{label}]", text, flags=flags)
        counts[label.lower()] += count

    replace(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", "CREDENCIAL", re.IGNORECASE)
    replace(r"\bsk-[A-Za-z0-9_-]{12,}", "CREDENCIAL")
    replace(
        r"\b(?:contraseña|password|clave|token|api[_ -]?key|secret)"
        r"\s*(?::|=|\bes\b)\s*(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s,;]+)",
        "CREDENCIAL",
        re.IGNORECASE,
    )
    replace(r"https?://[^\s<>]+|www\.[^\s<>]+", "ENLACE", re.IGNORECASE)
    replace(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", "CORREO", re.IGNORECASE)
    replace(
        r"(?m)^(?:nombre(?: completo)?|dirección(?: postal)?|domicilio)"
        r"\s*[:=]\s*[^\n]+",
        "DATO_PERSONAL",
        re.IGNORECASE,
    )
    replace(
        r"\b(?:cédula|cedula|dni|nif|ruc|rut|pasaporte|passport|"
        r"usuario|username|login)\s*[:=#]\s*[\w./-]+",
        "IDENTIFICADOR",
        re.IGNORECASE,
    )

    def redact_ip(match):
        try:
            ipaddress.ip_address(match.group())
        except ValueError:
            return match.group()
        counts["ip"] += 1
        return "[IP]"

    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", redact_ip, text)
    text = re.sub(
        r"(?<![\w:])[0-9a-fA-F]*:[0-9a-fA-F:]+(?![\w:])",
        redact_ip,
        text,
    )
    replace(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b", "CUENTA")

    def redact_number(match):
        value = match.group()
        digits = re.sub(r"\D", "", value)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        if not 8 <= len(digits) <= 19:
            return value
        counts["numero_privado"] += 1
        return "[NUMERO_PRIVADO]"

    text = re.sub(r"(?<!\w)\+?\d[\d(). \t-]{5,}\d(?!\w)", redact_number, text)
    return text


def sanitize_ticket(title, body):
    """Return sanitized subject/body and non-sensitive processing counters."""
    title, _ = plain_email(title)
    body, html_signature = plain_email(body)
    body, text_signature = remove_signature(body)
    counts = Counter()
    title = redact_sensitive(title, counts).strip()
    body = redact_sensitive(body, counts).strip()
    if not title or not body:
        raise ValueError("No quedó título o cuerpo útil después de limpiar.")
    return {
        "titulo": title,
        "cuerpo": body,
        "limpieza": {
            "version": 1,
            "firma_eliminada": html_signature or text_signature,
            "datos_redactados": dict(counts),
        },
    }
