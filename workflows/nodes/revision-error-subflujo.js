// A reusable child receives its context explicitly from the calling workflow.
const context = $json.context || {};
const email = context.email || {};
return { json: {
  estado: 'pendiente_revision',
  asunto: email.asunto || 'Solicitud de soporte',
  message_id: email.message_id,
  motivo: 'No se completó el procesamiento. Revisar la ejecución y comprobar si Redmine creó el ticket antes de reintentar.',
  origen: context.origen || {},
  contexto_aviso: { email, raw: context.raw || {} },
} };
