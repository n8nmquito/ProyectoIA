const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const workflow = JSON.parse(fs.readFileSync(path.join(__dirname, 'correo-ia-redmine-python300.json'), 'utf8'));
const nodes = Object.fromEntries(workflow.nodes.map(node => [node.name, node]));
function run(name, input, previous) {
  return vm.runInNewContext(`(function(){${nodes[name].parameters.jsCode}\n})()`, {
    $json: input, $: name => ({ item: { json: previous[name] } }),
  }, { timeout: 1000 }).json;
}
assert.equal(nodes['Limpiar firma y datos'].type, 'n8n-nodes-base.code');
assert.equal(nodes['Clasificar correo - Modelo 300'], undefined);
assert.equal(nodes['Usar correo limpio - Python'], undefined);
assert.equal(workflow.connections['Normalizar correo'].main[0][0].node, 'Limpiar firma y datos');
assert.equal(workflow.connections['Consultar API - Modelo 300'].main[0][0].node, 'Unir correo y predicción');
assert.equal(workflow.connections['Unir correo y predicción'].main[0][0].node, 'Seleccionar adjuntos para IA');
assert.match(nodes['Seleccionar adjuntos para IA'].parameters.jsCode, /clasificación válida/);
const ml = { categoria: 'otros', confianza: 0.9986, requiere_revision: false,
  muestras_entrenamiento: 300, modelo_version: 'modelo_clasificador_300',
  datos_entrenamiento: 'correos_300.json', estado: 'clasificado' };
const agent = { categoria: 'aplicaciones', requiere_revision: false,
  descripcion: 'Solicitud de capacitación en JDE.', assigned_to_id: 10,
  membership_id: 110, role_id: 5, motivo_asignacion: 'Aplicaciones' };
function apply(prediction = ml, analysis = agent) {
  return run('Aplicar categoría Python', { output: analysis }, {
    'Consultar API - Modelo 300': prediction,
  });
}
const applied = apply();
assert.equal(applied.output.categoria, 'otros');
assert.equal(applied.output.assigned_to_id, 0);
assert.equal(applied.output.requiere_revision, true);
assert.equal(applied.comparacion_tecnicas.categoria_llm, 'aplicaciones');
assert.equal(applied.comparacion_tecnicas.autoridad_categoria, 'python');
assert.match(applied.output.descripcion, /Python: Otros/);
const aligned = { ...agent, categoria: 'otros' };
assert.equal(apply(ml, aligned).output.requiere_revision, false);
assert.equal(apply({ ...ml, confianza: 0.4, requiere_revision: true }, aligned).output.requiere_revision, true);
for (const prediction of [null, {}, { ...ml, categoria: '__proto__' },
  { ...ml, estado: 'clasificacion_no_disponible' }, { ...ml, confianza: NaN },
  { ...ml, confianza: 2 }, { ...ml, modelo_version: 'otro' }]) {
  assert.throws(() => apply(prediction), /Python no devolvió una categoría válida/);
}
const proposal = { issue: { project_id: 1, category_id: 4, subject: 'Capacitación JDE', description: 'Correo' },
  routing: { category: 'otros', user_id: 10, membership_id: 110, role_id: 5 } };
const categories = { statusCode: 200, body: { issue_categories: [
  { id: 4, name: 'Otros', project: { id: 1 }, assigned_to: { id: 12 } },
] } };
const member = { id: 112, project: { id: 1 }, user: { id: 12, name: 'Soporte General' }, roles: [{ id: 7 }] };
const members = { statusCode: 200, body: { memberships: [member] } };
function resolve(input = members, catalog = categories, inputProposal = proposal) {
  return run('Resolver responsable por categoría', input, {
    'Validar proyecto y tipo': inputProposal,
    'Consultar categorías para asignación': catalog,
  });
}
const resolved = resolve();
assert.equal(resolved.routing.user_id, 12);
assert.equal(resolved.routing.membership_id, 112);
assert.equal(resolved.routing.role_id, 7);
assert.match(resolved.routing.reason, /categoría final de Python: Otros/);
assert.throws(() => resolve({ statusCode: 403 }), /consultar categorías o miembros/);
assert.throws(() => resolve({ statusCode: 200, body: { memberships: [] } }), /membresía única/);
const wrongProject = structuredClone(categories);
wrongProject.body.issue_categories[0].project.id = 99;
assert.throws(() => resolve(members, wrongProject), /no corresponde/);
const role = { statusCode: 200, body: { role: { id: 7, name: 'Soporte', assignable: true, permissions: ['view_issues'] } } };
const links = { 'Resolver responsable por categoría': resolved,
  'Verificar membresía elegida': { statusCode: 200, body: { membership: member } } };
assert.equal(run('Validar responsable real', role, links).issue.assigned_to_id, 12);
const forbiddenRole = structuredClone(role);
forbiddenRole.body.role.assignable = false;
assert.throws(() => run('Validar responsable real', forbiddenRole, links), /No se creó ticket/);
assert.match(nodes['Agente IA - Analizar solicitud'].parameters.text, /categoria_final_python/);
assert.match(nodes['Agente IA - Analizar solicitud'].parameters.options.systemMessage, /copia exactamente/);
assert.match(nodes['Verificar rol asignable'].parameters.url, /Resolver responsable por categoría/);
assert.equal(workflow.active, false);
assert.deepEqual(workflow.pinData, {});
for (const node of workflow.nodes) assert.equal(node.credentials, undefined);
for (const links of Object.values(workflow.connections)) for (const outputs of Object.values(links))
  for (const output of outputs) for (const link of output) assert.ok(nodes[link.node], link.node);
for (const name of ['Aplicar categoría Python', 'Consultar categorías para asignación',
  'Consultar miembros para asignación', 'Resolver responsable por categoría']) {
  assert.equal(workflow.connections[name].main[1][0].node, 'Sin análisis IA - Revisión');
}
console.log('OK: Python final, desacuerdo, baja confianza, API inválida, responsable por categoría, rol verificado y conexiones.');
