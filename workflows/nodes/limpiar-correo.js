// n8n Code node: redact subject/body locally, preserving original attachments.
const original = $input.item;
const counts = {};
let signatureRemoved = false;
function plain(value) {
  if (typeof value !== 'string') throw new Error('El asunto y cuerpo deben ser texto.');
  let text = value.replace(/\r\n?/g, '\n');
  // Remove marked signature containers before stripping HTML tags.
  text = text.replace(/<(div|span|table)\b[^>]*(?:class|id)\s*=\s*["'][^"']*(?:gmail_signature|moz-signature|signature)[^"']*["'][^>]*>[\s\S]*$/gi, () => {
    signatureRemoved = true;
    return '';
  });
  return text.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, '')
    .replace(/<\/?(?:p|div|br|li|tr|hr)\b[^>]*>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&(?:nbsp|amp|lt|gt|quot|apos);/gi, entity => ({
      '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'",
    })[entity.toLowerCase()])
    .replace(/&#(x[0-9a-f]+|\d+);/gi, (match, code) => {
      const point = /^x/i.test(code) ? parseInt(code.slice(1), 16) : Number(code);
      return point > 0 && point <= 0x10ffff ? String.fromCodePoint(point) : '';
    });
}
function redact(value) {
  let text = value;
  function replace(pattern, label) {
    text = text.replace(pattern, () => {
      counts[label.toLowerCase()] = (counts[label.toLowerCase()] || 0) + 1;
      return `[${label}]`;
    });
  }
  replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, 'CREDENCIAL');
  replace(/\bsk-[A-Za-z0-9_-]{12,}/g, 'CREDENCIAL');
  replace(/\b(?:contraseña|password|clave|token|api[_ -]?key|secret)\s*(?::|=|\bes\b)\s*(?:"[^"\n]*"|'[^'\n]*'|[^\s,;]+)/gi, 'CREDENCIAL');
  replace(/https?:\/\/[^\s<>]+|www\.[^\s<>]+/gi, 'ENLACE');
  replace(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/gi, 'CORREO');
  replace(/^(?:nombre(?: completo)?|dirección(?: postal)?|domicilio)\s*[:=]\s*[^\n]+/gim, 'DATO_PERSONAL');
  replace(/\b(?:cédula|cedula|dni|nif|ruc|rut|pasaporte|passport|usuario|username|login)\s*[:=#]\s*[\w./-]+/gi, 'IDENTIFICADOR');
  replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, 'IP');
  replace(/(?<![\w:])(?:[a-f\d]{0,4}:){2,}[a-f\d:]{0,39}(?![\w:])/gi, 'IP');
  replace(/\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b/g, 'CUENTA');
  text = text.replace(/(?<!\w)\+?\d[\d(). \t-]{5,}\d(?!\w)/g, value => {
    const length = value.replace(/\D/g, '').length;
    if (/^\d{4}-\d{2}-\d{2}$/.test(value) || length < 8 || length > 19) return value;
    counts.numero_privado = (counts.numero_privado || 0) + 1;
    return '[NUMERO_PRIVADO]';
  });
  return text.trim();
}
let body = plain(original.json.html_para_limpieza || original.json.cuerpo);
const lines = body.split('\n');
for (let index = 0; index < lines.length; index++) {
  const line = lines[index].trim();
  const hasContent = lines.slice(0, index).some(previous => previous.trim());
  const signoff = /^(?:saludos(?: cordiales)?|cordialmente|atentamente|un saludo|gracias y saludos|best regards|kind regards|regards|sincerely)[,.!\s]*$/i.test(line) && lines.length - index <= 15;
  const footer = /^(?:aviso de confidencialidad|confidentiality notice|este (?:mensaje|correo).{0,100}confidencial|this (?:message|e-?mail).{0,100}confidential)/i.test(line);
  if (hasContent && (line === '--' || /^(?:enviado desde|sent from my)\b/i.test(line) || signoff || footer)) {
    body = lines.slice(0, index).join('\n');
    signatureRemoved = true;
    break;
  }
}
const subject = redact(plain(original.json.asunto));
body = redact(body);
if (!subject || !body) throw new Error('No quedó asunto o cuerpo útil después de limpiar. Revisar manualmente.');
const { html_para_limpieza, ...email } = original.json;
return { json: { ...email, asunto: subject, cuerpo: body,
  limpieza: { version: 2, firma_eliminada: signatureRemoved, datos_redactados: counts },
}, ...(original.binary ? { binary: original.binary } : {}) };
