let result = $json.output;
if (typeof result === 'string') result = JSON.parse(result);
if (!result || !['crear_ticket','omitir'].includes(result.accion_correo) || typeof result.motivo_decision !== 'string' || !result.motivo_decision.trim()) throw new Error('No hay una decisión de correo válida. Revisar la ejecución; no se creó ticket.');
return {json:{...$json,output:result,crear_ticket:result.accion_correo==='crear_ticket'}};
