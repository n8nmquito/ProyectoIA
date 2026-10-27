const proposal = $('Preparar ticket - Intaco').item.json;
const response = $json;
const project = response.body?.project;
if (response.statusCode !== 200 || !project || project.id !== proposal.issue.project_id || project.status !== 1) {
  throw new Error('El proyecto propuesto no existe, está inactivo o la credencial no puede consultarlo. No se creó el ticket.');
}
const issue = { ...proposal.issue };
const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
const requestedType = normalize(proposal.routing.tracker_name);
if (!['errores','soporte'].includes(requestedType)) {
  throw new Error('Tipo de ticket fuera del catálogo permitido. No se creó el ticket.');
}
const enabledTypes = (project.trackers || []).filter(t => normalize(t.name) === requestedType);
if (enabledTypes.length !== 1 || !Number.isSafeInteger(enabledTypes[0].id) || enabledTypes[0].id < 1) {
  throw new Error('El tipo solicitado no está habilitado o es ambiguo en el proyecto. No se creó el ticket.');
}
issue.tracker_id = enabledTypes[0].id;
const matches = (project.issue_categories || []).filter(category => normalize(category.name) === normalize(proposal.routing.category));
if (matches.length !== 1 || !Number.isSafeInteger(matches[0].id) || matches[0].id < 1) {
  throw new Error('La categoría "' + proposal.routing.category + '" no existe o es ambigua en el proyecto ' + project.id + '. Configurar sus categorías en Redmine. No se creó el ticket.');
}
issue.category_id = matches[0].id;
if (!proposal.routing.user_id) {
  delete issue.assigned_to_id;
  if (!issue.subject.includes('[REVISAR]')) issue.subject = ('[REVISAR] ' + issue.subject).slice(0, 255);
  issue.description += '\n\nASIGNACIÓN: sin responsable verificado; requiere revisión humana.';
}
return { json: { ...proposal, issue } };
