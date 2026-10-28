const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const workflow = JSON.parse(fs.readFileSync(path.join(__dirname,
  'correo-ia-redmine-python300.json'), 'utf8'));
const nodes = Object.fromEntries(workflow.nodes.map(node => [node.name, node]));
const source = file => fs.readFileSync(path.join(__dirname, 'nodes', file), 'utf8');
function execute(code, json, previous = {}) {
  const result = vm.runInNewContext(`(function(){${code}\n})()`, {
    $json: json,
    $: name => {
      if (!previous[name]) throw new Error('Sin contexto: ' + name);
      return { item: { json: previous[name] } };
    },
  }, { timeout: 1000 });
  return JSON.parse(JSON.stringify(result.json));
}
const run = (name, json, previous) => execute(nodes[name].parameters.jsCode,
  json, previous);
assert.equal(workflow.nodes.length, 41);
for (const name of ['Aplicar categoría Python', 'Preparar aviso - Ticket creado',
  'Preparar aviso - Error de procesamiento']) assert.equal(nodes[name], undefined);
for (const [name, outputs] of Object.entries(workflow.connections)) {
  assert.ok(nodes[name], name);
  for (const branches of Object.values(outputs)) for (const branch of branches)
    for (const edge of branch) {
      assert.ok(nodes[edge.node], edge.node);
      assert.notEqual(name, edge.node, 'No se admiten bucles accidentales');
    }
}
// Comprobar igualdad frente a las dos etapas anteriores, con varios correos.
for (const sender of ['persona@prueba.test', 'demo@example.invalid',
  'no-reply@prueba.test', 'n8n.mquito@gmail.com', 'dirección inválida']) {
  const email = { remitente: sender, asunto: 'Error en JDE',
    cuerpo: 'No guarda la orden.\nFirma privada\npassword: secreto-no-publicar',
    message_id: sender, fecha: '2026-10-28' };
  const cleanEmail = { ...email, asunto: 'Error en JDE (limpio)',
    cuerpo: 'No guarda la orden. Texto limpio.', limpieza: { version: 3 } };
  const previous = { 'Normalizar correo': email, 'Limpiar firma y datos': cleanEmail,
    'Leer buzón IMAP': { from: sender, subject: email.asunto } };
  const expectedError = execute(source('notificacion-error.js'), {
    estado: 'pendiente_revision', asunto: email.asunto, message_id: sender,
    motivo: 'No se completó el procesamiento. Revisar la ejecución y comprobar si Redmine creó el ticket antes de reintentar.',
  }, previous);
  assert.deepEqual(run('Sin análisis IA - Revisión', {}, previous), expectedError);
  const expectedTicket = execute(source('notificacion-ticket.js'), {
    ticket_id: 123, asunto: 'Ticket de prueba',
    url: 'http://185.208.207.203:3000/issues/123', estado: 'creado',
  }, previous);
  assert.deepEqual(run('Resultado del ticket', { issue: {
    id: 123, subject: 'Ticket de prueba' } }, previous), expectedTicket);
  for (const category of ['accesos', 'aplicaciones', 'infraestructura', 'otros']) {
    const analysis = { categoria: 'aplicaciones', requiere_revision: false,
      resumen: 'Error de prueba', descripcion: 'No guarda la orden.',
      prioridad: 'alta', datos_faltantes: [], project_id: 1,
      assigned_to_id: 10, membership_id: 110, role_id: 5,
      motivo_asignacion: 'Responsable configurado', tipo_ticket: 'Errores' };
    const ml = { categoria: category, confianza: 0.9,
      requiere_revision: false, muestras_entrenamiento: 300,
      modelo_version: 'modelo_clasificador_300', estado: 'clasificado' };
    const links = { ...previous, 'Consultar API - Modelo 300': ml };
    const applied = execute(source('aplicar-categoria-python.js'),
      { output: analysis }, links);
    const currentPreparation = source('preparar-ticket.js')
      .replace('Categoría sugerida', 'Categoría final (Python)')
      .replace("const email = $('Normalizar correo').item.json;",
        "const email = $('Normalizar correo').item.json; const cleanEmail = $('Limpiar firma y datos').item.json;")
      .replace("['Asunto original',email.asunto]", "['Asunto (limpio)',cleanEmail.asunto]")
      .replace("'## Texto del correo'", "'## Texto del correo (limpio)'")
      .replace("String(email.cuerpo||'')", "String(cleanEmail.cuerpo||'')");
    const expected = execute(currentPreparation, applied, links);
    const prepared = run('Preparar ticket - Intaco', { output: analysis }, links);
    assert.deepEqual(prepared, expected);
    assert.ok(!prepared.issue.description.includes('Firma privada'));
    assert.ok(!prepared.issue.description.includes('secreto-no-publicar'));
    assert.throws(() => run('Preparar ticket - Intaco', { output: analysis }, {
      ...links, 'Limpiar firma y datos': { cuerpo: '' },
    }), /Falta el texto limpio/);
    assert.throws(() => run('Preparar ticket - Intaco', { output: analysis }, {
      ...links, 'Consultar API - Modelo 300': { ...ml, estado: 'error' },
    }), /Python no devolvió una categoría válida/);
  }
}
assert.throws(() => run('Resultado del ticket', { issue: {} }),
  /Redmine no devolvió el ID/);
const fallback = run('Sin análisis IA - Revisión', {}, {
  'Leer buzón IMAP': { from: 'demo@example.invalid', subject: 'Prueba' },
});
assert.equal(fallback.estado, 'pendiente_revision');
assert.equal(fallback.notificacion.enviar, false);
const positions = new Set(workflow.nodes.map(node => node.position.join(',')));
assert.equal(positions.size, 41, 'Los nodos no deben superponerse');
console.log('OK: 41 nodos, tres fusiones equivalentes, cuatro categorías, avisos, errores y posiciones.');
