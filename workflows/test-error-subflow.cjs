const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const read = name => fs.readFileSync(path.join(__dirname, name), 'utf8');
const parent = JSON.parse(read('correo-ia-redmine-python300.json'));
const child = JSON.parse(read('revision-aviso-error.json'));
const byName = Object.fromEntries(child.nodes.map(node => [node.name, node]));
const execute = (code, json, linked = {}) => vm.runInNewContext(`(function(){${code}\n})()`, {
  $json: json,
  $: name => { if (!(name in linked)) throw new Error('Nodo no ejecutado'); return { item: { json: linked[name] } }; },
}, { timeout: 1000 }).json;
const contextCode = read('nodes/contexto-error.js');
const contextFor = (email, raw) => vm.runInNewContext(`(function(){${contextCode}\n})()`, {
  $workflow: { id: 'parent-fixture', name: 'Flujo de prueba' },
  $execution: { id: 'execution-fixture' },
  $: name => {
    const json = name === 'Normalizar correo' ? email : raw;
    if (json === undefined) throw new Error('Nodo no ejecutado');
    return { item: { json } };
  },
}, { timeout: 1000 });
const reviewCode = byName['Sin análisis IA - Revisión'].parameters.jsCode;
const noticeCode = byName['Preparar aviso - Error de procesamiento'].parameters.jsCode;
const previousNotice = read('nodes/notificacion-error.js');
const cases = [
  { email: { remitente: 'persona@prueba.test', asunto: 'Error JDE', message_id: 'one' }, raw: {}, send: true },
  { email: { remitente: 'persona@prueba.test', asunto: 'Demo', demo: true }, raw: {}, send: false },
  { email: { remitente: 'persona@example.invalid' }, raw: {}, send: false },
  { email: { remitente: 'n8n.mquito@gmail.com' }, raw: {}, send: false },
  { email: { remitente: 'no-reply@prueba.test' }, raw: {}, send: false },
  { email: { remitente: 'persona@prueba.test' }, raw: { headers: { 'Auto-Submitted': 'auto-generated' } }, send: false },
  { email: { remitente: 'persona@prueba.test\r\nBcc: victim@prueba.test' }, raw: {}, send: false },
  { email: undefined, raw: { from: 'Persona <persona@prueba.test>', subject: 'Sin normalizar' }, send: true },
  { email: undefined, raw: {}, send: false },
];
for (const test of cases) {
  const context = contextFor(test.email, test.raw);
  const review = execute(reviewCode, { context });
  const actual = execute(noticeCode, review);
  const links = { 'Leer buzón IMAP': test.raw };
  if (test.email !== undefined) links['Normalizar correo'] = test.email;
  const previous = execute(previousNotice, { estado: 'pendiente_revision' }, links);
  assert.deepEqual(JSON.parse(JSON.stringify(actual.notificacion)), JSON.parse(JSON.stringify(previous.notificacion)));
  assert.equal(actual.notificacion.enviar, test.send);
  assert.equal(actual.estado, 'pendiente_revision');
  assert.equal(actual.origen.execution_id, 'execution-fixture');
  assert.equal(actual.contexto_aviso, undefined);
}
const context = contextFor({ remitente: 'demo@example.invalid', cuerpo: 'private-body' }, {
  textPlain: 'private-body', headers: { authorization: 'private-key', precedence: 'bulk' },
});
assert.ok(!JSON.stringify(context).includes('private-body'));
assert.ok(!JSON.stringify(context).includes('private-key'));
const caller = parent.nodes.find(node => node.name === 'Revisión y aviso - Subflujo');
assert.equal(caller.type, 'n8n-nodes-base.executeWorkflow');
assert.equal(caller.parameters.options.waitForSubWorkflow, true);
assert.equal(caller.parameters.workflowInputs.schema[0].type, 'object');
assert.equal(parent.nodes.length, 41);
assert.equal(child.nodes.length, 6);
const removed = ['Sin análisis IA - Revisión', 'Preparar aviso - Error de procesamiento',
  '¿Notificar? - Error de procesamiento', 'Notificar - Error de procesamiento'];
assert.ok(parent.nodes.every(node => !removed.includes(node.name)));
const links = Object.values(parent.connections).flatMap(outputs => Object.values(outputs).flat(2));
assert.equal(links.filter(link => link.node === caller.name).length, 22);
assert.equal(child.nodes[0].type, 'n8n-nodes-base.executeWorkflowTrigger');
assert.equal(byName['Notificar - Error de procesamiento'].onError, 'continueRegularOutput');
for (const node of child.nodes) {
  assert.equal(node.credentials, undefined);
  const code = node.parameters.jsCode || '';
  assert.ok(!code.includes("$('Normalizar correo')"));
  assert.ok(!code.includes("$('Leer buzón IMAP')"));
}
assert.equal(child.active, false);
assert.deepEqual(child.pinData, {});
console.log('OK: subflujo autónomo, 22 rutas, filtros originales, contexto mínimo y devolución de revisión.');
