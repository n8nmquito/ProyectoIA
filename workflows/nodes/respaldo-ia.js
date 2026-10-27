let email={};try{email=$('Normalizar correo').item.json;}catch{}
return {json:{estado:'pendiente_revision',asunto:email.asunto||'Solicitud de soporte',message_id:email.message_id,motivo:'No se completó el procesamiento. Revisar la ejecución y comprobar si Redmine creó el ticket antes de reintentar.'}};
