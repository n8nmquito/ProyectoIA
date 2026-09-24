const proposal = $('Validar proyecto y tipo').item.json;
const membershipResponse = $('Verificar membresía elegida').item.json;
const membership = membershipResponse.body?.membership;
const role = $json.body?.role;
const routing = proposal.routing;
const valid = membershipResponse.statusCode === 200 && $json.statusCode === 200 &&
  membership?.project?.id === proposal.issue.project_id &&
  membership?.user?.id === routing.user_id &&
  membership?.id === routing.membership_id &&
  membership.roles?.some(r => r.id === routing.role_id) &&
  role?.id === routing.role_id && role.assignable === true &&
  Array.isArray(role.permissions) && role.permissions.includes('view_issues');
const issue = { ...proposal.issue };
if (valid) {
  issue.assigned_to_id = routing.user_id;
  issue.description += '\n\nASIGNACIÓN VALIDADA\nResponsable: ' + membership.user.name +
    ' (ID ' + routing.user_id + ')\nRol: ' + role.name +
    '\nMotivo sugerido por IA: ' + routing.reason;
} else {
  delete issue.assigned_to_id;
  if (!issue.subject.includes('[REVISAR]')) issue.subject = ('[REVISAR] ' + issue.subject).slice(0, 255);
  issue.description += '\n\nASIGNACIÓN NO APLICADA: la membresía/rol propuestos no pudieron verificarse. Ticket sin responsable para revisión humana.';
}
return { json: { issue } };
