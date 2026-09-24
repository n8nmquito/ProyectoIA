const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function run(file, data, links) {
  const code = fs.readFileSync(path.join(__dirname, 'nodes', file), 'utf8');
  return vm.runInNewContext('(function(){' + code + '\n})()', {
    $json: data, $: name => ({ item: { json: links[name] } }),
  }, { timeout: 1000 }).json;
}
const proposal = { issue: { project_id: 1, tracker_id: 3, subject: 'Prueba', description: 'Correo' },
  routing: { user_id: 6, membership_id: 2, role_id: 4, reason: 'Rol técnico consultado en la API.' } };
const project = { statusCode: 200, body: { project: { id: 1, status: 1, trackers: [{ id: 3 }] } } };
const validProject = run('validar-proyecto.js', project, { 'Preparar ticket - Intaco': proposal });
assert.equal(validProject.routing.user_id, 6);
for (const bad of [
  { statusCode: 403, body: {} },
  { statusCode: 200, body: { project: { id: 2, status: 1, trackers: [{ id: 3 }] } } },
  { statusCode: 200, body: { project: { id: 1, status: 5, trackers: [{ id: 3 }] } } },
  { statusCode: 200, body: { project: { id: 1, status: 1, trackers: [] } } },
]) assert.throws(() => run('validar-proyecto.js', bad, { 'Preparar ticket - Intaco': proposal }));
const noUser = run('validar-proyecto.js', project, { 'Preparar ticket - Intaco': { ...proposal, routing: { ...proposal.routing, user_id: 0 } } });
assert.equal(noUser.issue.assigned_to_id, undefined);
assert.match(noUser.issue.subject, /REVISAR/);

const membership = { statusCode: 200, body: { membership: {
  id: 2, project: { id: 1 }, user: { id: 6, name: 'Técnico de prueba' }, roles: [{ id: 4 }],
} } };
const role = { statusCode: 200, body: { role: { id: 4, name: 'Desarrollador', assignable: true, permissions: ['view_issues'] } } };
const validate = (m = membership, r = role) => run('validar-asignacion.js', r, {
  'Validar proyecto y tipo': validProject, 'Verificar membresía elegida': m,
});
assert.equal(validate().issue.assigned_to_id, 6);
for (const mutate of [
  m => { m.body.membership.user.id = 999; },
  m => { m.body.membership.project.id = 2; },
  m => { m.body.membership.roles = [{ id: 5 }]; },
  m => { delete m.body.membership.user; m.body.membership.group = { id: 6 }; },
  m => { m.statusCode = 403; },
]) {
  const altered = structuredClone(membership); mutate(altered);
  const result = validate(altered);
  assert.equal(result.issue.assigned_to_id, undefined);
  assert.match(result.issue.subject, /REVISAR/);
}
for (const mutate of [r => { r.body.role.assignable = false; }, r => { r.body.role.permissions = []; }, r => { r.body.role.id = 5; }]) {
  const altered = structuredClone(role); mutate(altered);
  assert.equal(validate(membership, altered).issue.assigned_to_id, undefined);
}
const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'correo-ia-redmine.json'), 'utf8'));
const tools = wf.nodes.filter(n => n.type === 'n8n-nodes-base.httpRequestTool');
assert.equal(tools.length, 5);
for (const tool of tools) {
  assert.equal(tool.parameters.method, 'GET');
  assert.equal(tool.parameters.genericAuthType, 'httpHeaderAuth');
  assert.ok(tool.parameters.url.includes('http://redmine:3000/'));
  assert.equal(wf.connections[tool.name].ai_tool[0][0].node, 'Agente IA - Analizar solicitud');
  assert.equal(tool.credentials, undefined);
}
console.log('OK: proyecto/tipo, membresía real, roles asignables, rechazo de usuarios/grupos ajenos y herramientas GET.');
