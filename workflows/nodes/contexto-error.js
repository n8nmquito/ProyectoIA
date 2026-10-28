// Pass only notification metadata; sub-workflows cannot read parent nodes.
let email = {};
let raw = {};
try { email = $('Normalizar correo').item.json; } catch {}
try { raw = $('Leer buzón IMAP').item.json; } catch {}
const headers = Object.fromEntries(Object.entries(raw.headers || raw.metadata || {})
  .filter(([key]) => ['auto-submitted', 'precedence', 'list-id'].includes(key.toLowerCase())));
return {
  email: {
    remitente: email.remitente, asunto: email.asunto,
    message_id: email.message_id, demo: email.demo === true,
  },
  raw: { from: raw.from, subject: raw.subject, headers },
  origen: {
    workflow_id: $workflow.id, workflow_nombre: $workflow.name,
    execution_id: $execution.id,
  },
};
