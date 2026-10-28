// Resolve the configured category owner using fresh Redmine catalog data.
const proposal = $('Validar proyecto y tipo').item.json;
const categoryResponse = $('Consultar categorías para asignación').item.json;
const memberResponse = $json;
if (categoryResponse.statusCode !== 200 || memberResponse.statusCode !== 200
    || !Array.isArray(categoryResponse.body?.issue_categories)
    || !Array.isArray(memberResponse.body?.memberships)) {
  throw new Error('No se pudieron consultar categorías o miembros. No se creó el ticket.');
}
const category = categoryResponse.body.issue_categories.find(
  entry => entry.id === proposal.issue.category_id,
);
const normalize = value => String(value ?? '').normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
if (!category || category.project?.id !== proposal.issue.project_id
    || normalize(category.name) !== normalize(proposal.routing.category)) {
  throw new Error('La categoría consultada no corresponde al proyecto y a Python.');
}
const owner = category.assigned_to?.id;
if (owner !== undefined && (!Number.isSafeInteger(owner) || owner < 1)) {
  throw new Error('El responsable configurado de la categoría no es válido.');
}
const issue = { ...proposal.issue };
const routing = { ...proposal.routing, category_owner_id: owner || null };
const user = owner || routing.user_id;
if (!user) {
  delete issue.assigned_to_id;
  issue.priority_id = 2;
  if (!issue.subject.includes('[REVISAR]')) issue.subject = ('[REVISAR] ' + issue.subject).slice(0, 255);
  issue.description += '\n\nASIGNACIÓN: sin responsable configurado ni propuesta verificable; requiere revisión humana.';
  return { json: { ...proposal, issue, routing } };
}
const memberships = memberResponse.body.memberships.filter(
  member => member.project?.id === issue.project_id && member.user?.id === user,
);
if (memberships.length !== 1) {
  throw new Error('No se encontró una membresía única del responsable; revisar membresías y paginación. No se creó ticket.');
}
const member = memberships[0];
const roles = (member.roles || []).filter(role => Number.isSafeInteger(role.id) && role.id > 0);
const role = roles.find(role => role.id === routing.role_id) || roles[0];
if (!Number.isSafeInteger(member.id) || member.id < 1 || !role) {
  throw new Error('El responsable no tiene una membresía y rol verificables.');
}
routing.user_id = user;
routing.membership_id = member.id;
routing.role_id = role.id;
if (owner) routing.reason = 'Responsable configurado en Redmine para la categoría final de Python: ' + category.name + '.';
return { json: { ...proposal, issue, routing } };
