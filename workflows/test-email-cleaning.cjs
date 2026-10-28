const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const code = fs.readFileSync(path.join(__dirname, 'nodes/limpiar-correo.js'), 'utf8');
function clean(json, binary) {
  return vm.runInNewContext(`(function(){${code}\n})()`, {
    $input: { item: { json, binary } },
  }, { timeout: 1000 });
}
const binary = { attachment: { fileName: 'ejemplo.pdf', data: 'cHJ1ZWJh' } };
const email = { asunto: 'Error de maria@example.test',
  cuerpo: 'No guarda la orden JDE.\nIP: 192.168.1.10 y 2001:db8::1\npassword: pruebaSecreta\nTel: +506 8888-9999\n\nSaludos cordiales,\nMaría Prueba',
  remitente: 'sender@example.test', message_id: 'synthetic' };
const result = clean(email, binary);
assert.match(result.json.cuerpo, /No guarda la orden JDE/);
for (const sensitive of ['192.168.1.10', '2001:db8::1', 'pruebaSecreta', '8888', 'María Prueba']) {
  assert.ok(!result.json.cuerpo.includes(sensitive), sensitive);
}
assert.equal(result.json.asunto, 'Error de [CORREO]');
assert.equal(result.json.limpieza.firma_eliminada, true);
assert.equal(result.json.limpieza.datos_redactados.ip, 2);
assert.equal(result.binary, binary);
assert.equal(result.json.remitente, email.remitente);
assert.match(email.cuerpo, /pruebaSecreta/); // Original retained for Redmine only.
const html = clean({ asunto: 'Ayuda', cuerpo: 'Versión normalizada',
  html_para_limpieza: '<p>No guarda &amp; falla.</p><div class="gmail_signature"><p>Nombre privado</p></div>',
});
assert.equal(html.json.cuerpo, 'No guarda & falla.');
assert.equal(html.json.html_para_limpieza, undefined);
assert.equal(html.json.limpieza.firma_eliminada, true);
for (const ending of ['--\nFirma', 'Sent from my phone', 'Aviso de confidencialidad']) {
  assert.equal(clean({ asunto: 'Ayuda', cuerpo: `Error al guardar.\n${ending}` }).json.cuerpo, 'Error al guardar.');
}
assert.match(clean({ asunto: 'Ayuda', cuerpo: 'Error 500 el 2026-10-28.' }).json.cuerpo, /500 el 2026-10-28/);
assert.throws(() => clean({ asunto: 'Ayuda', cuerpo: '' }), /No quedó/);
assert.throws(() => clean({ asunto: 'Ayuda', cuerpo: 123 }), /deben ser texto/);
assert.throws(() => clean({ asunto: 'Ayuda', cuerpo: '<div class="signature">Firma</div>' }), /No quedó/);
console.log('OK: limpieza local, firmas, HTML, datos sensibles, contexto y adjuntos preservados, errores sin respaldo.');
