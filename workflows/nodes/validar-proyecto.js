const proposal = $('Preparar ticket - Intaco').item.json;
const response = $json;
const project = response.body?.project;
if (response.statusCode !== 200 || !project || project.id !== proposal.issue.project_id || project.status !== 1) {
  throw new Error('El proyecto propuesto no existe, está inactivo o la credencial no puede consultarlo. No se creó el ticket.');
}
if (!Array.isArray(project.trackers) || !project.trackers.some(t => t.id === proposal.issue.tracker_id)) {
  throw new Error('El tipo de ticket propuesto no está habilitado en el proyecto. No se creó el ticket.');
}
const issue = { ...proposal.issue };
if (!proposal.routing.user_id) {
  delete issue.assigned_to_id;
  if (!issue.subject.includes('[REVISAR]')) issue.subject = ('[REVISAR] ' + issue.subject).slice(0, 255);
  issue.description += '\n\nASIGNACIÓN: sin responsable verificado; requiere revisión humana.';
}
return { json: { ...proposal, issue } };
