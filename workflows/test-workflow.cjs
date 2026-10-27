const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'correo-ia-redmine.json'), 'utf8'));
const byName = Object.fromEntries(wf.nodes.map(n => [n.name, n]));
const run = (name, input, previous) => vm.runInNewContext(
  `(function(){${byName[name].parameters.jsCode}\n})()`,
  { $json: input, $input: { item: { json: input, binary: {} } }, $: () => ({ item: { json: previous } }) },
  { timeout: 1000 },
).json;

const email = run('Normalizar correo', {
  from: { value: [{ address: 'test@example.com' }] },
  subject: 'Error de acceso', textPlain: 'Usuario bloqueado', messageId: 'mail-123',
});
assert.equal(email.remitente, 'test@example.com');
assert.equal(email.message_id, 'mail-123');
const html = run('Normalizar correo', { html: '<script>malicious()</script><p>Ayuda</p>' });
assert.equal(html.cuerpo, 'Ayuda');
assert.throws(() => run('Normalizar correo', { subject: 'Vacío' }), /sin texto/);
assert.equal(run('Normalizar correo', { text: 'x'.repeat(17000) }).cuerpo.length, 16000);
assert.equal(run('Normalizar correo', { text: 'x'.repeat(17000) }).texto_recortado, true);

const valid = { resumen: 'Acceso bloqueado', descripcion: 'Un usuario no puede entrar.',
  categoria: 'accesos', prioridad: 'alta', requiere_revision: false, datos_faltantes: [],
  project_id: 1, tipo_ticket: 'Soporte', assigned_to_id: 6, membership_id: 2, role_id: 4,
  motivo_asignacion: 'Rol técnico consultado en la API.' };
const result = run('Preparar ticket - Intaco', { output: valid }, email);
assert.equal(result.issue.project_id, 1);
assert.equal(result.issue.tracker_id, undefined);
assert.equal(result.routing.tracker_name, 'Soporte');
assert.equal(result.issue.priority_id, 3);
assert.match(result.issue.description, /Message-ID \| mail-123/);
const review = run('Preparar ticket - Intaco', { output: { ...valid, requiere_revision: true } }, email);
assert.equal(review.issue.priority_id, 2);
assert.match(review.issue.subject, /^\[REVISAR\]/);
assert.throws(() => run('Preparar ticket - Intaco', { output: { ...valid, prioridad: '__proto__' } }, email), /fuera del catálogo/);
assert.throws(() => run('Preparar ticket - Intaco', { output: 'not-json' }, email), /JSON válido/);
const injected = run('Preparar ticket - Intaco', { output: { ...valid, project_id: 999, url: 'http://invalid' } }, email);
assert.equal(injected.issue.project_id, 999); // Se valida después con GET del proyecto real.
assert.equal(injected.issue.url, undefined);
assert.equal(injected.issue.assigned_to_id, undefined); // Solo se aplica tras validar membresía y rol.
assert.throws(() => run('Resultado del ticket', {}), /no devolvió el ID/);
assert.equal(run('Resultado del ticket', { issue: { id: 42, subject: 'Prueba' } }).url, 'http://185.208.207.203:3000/issues/42');

assert.equal(wf.active, false);
assert.ok(wf.nodes.every(n => !n.credentials));
for (const links of Object.values(wf.connections)) for (const outputs of Object.values(links))
  for (const output of outputs) for (const link of output) assert.ok(byName[link.node]);
console.log('OK: normalización, límites, validación IA, revisión y conexiones.');
