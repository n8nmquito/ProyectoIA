let result = $json.output;
if (typeof result === 'string') { try { result = JSON.parse(result); } catch { throw new Error('La IA no devolvió JSON válido. No se creó un ticket.'); } }
if (!result || typeof result !== 'object') throw new Error('Falta la salida estructurada de IA.');
const categories = ['aplicaciones','infraestructura','accesos','otros'];
const priorities = { baja:1, normal:2, alta:3, urgente:4 };
for (const key of ['resumen','descripcion']) if (typeof result[key] !== 'string' || !result[key].trim()) throw new Error('Campo IA inválido: '+key);
if (!categories.includes(result.categoria) || !Object.hasOwn(priorities,result.prioridad)) throw new Error('Categoría o prioridad fuera del catálogo.');
if (!Array.isArray(result.datos_faltantes) || !result.datos_faltantes.every(v=>typeof v==='string') || typeof result.requiere_revision !== 'boolean') throw new Error('Salida IA incompleta.');
for (const key of ['project_id']) if (!Number.isSafeInteger(result[key]) || result[key] < 1) throw new Error('ID de proyecto/tipo inválido: '+key);
for (const key of ['assigned_to_id','membership_id','role_id']) if (!Number.isSafeInteger(result[key]) || result[key] < 0) throw new Error('ID de asignación inválido: '+key);
if (typeof result.motivo_asignacion !== 'string' || !result.motivo_asignacion.trim()) throw new Error('Falta motivo de asignación');
if (result.assigned_to_id > 0 && (!result.membership_id || !result.role_id)) throw new Error('Falta membresía o rol para validar la asignación');
if (!['Errores','Soporte'].includes(result.tipo_ticket)) throw new Error('Tipo de ticket fuera del catálogo permitido.');
const email = $('Normalizar correo').item.json;
// Correo real del remitente; nunca se toma de la respuesta de IA.
const sender = String(email.remitente || '').trim();
const addressMatch = sender.match(/<([^<>]+)>$/);
const requesterEmail = (addressMatch ? addressMatch[1] : sender).trim();
const validRequester = requesterEmail.length <= 254 && /^[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+$/.test(requesterEmail);

// Escape content so email text cannot break the Markdown tables.
const cell = value => String(value ?? 'No disponible').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\|/g,'&#124;').replace(/[\r\n]+/g,' ').replace(/([\\x60*_\[\]])/g,'\$1');
const table = rows => ['| Campo | Detalle |','| --- | --- |', ...rows.map(([key,value])=>'| '+key+' | '+cell(value)+' |')].join('\n');
const lines = [
 '## Datos del correo', '', table([
 ['Remitente',email.remitente],['Asunto original',email.asunto],['Fecha',email.fecha],['Message-ID',email.message_id]
 ]), '', '## Análisis de la solicitud', '', result.descripcion.slice(0,6000), '',
 table([['Categoría sugerida',result.categoria],['Prioridad sugerida',result.prioridad],['Prioridad aplicada',result.requiere_revision?'normal':result.prioridad],['Requiere revisión',result.requiere_revision?'Sí':'No'],['Datos faltantes',result.datos_faltantes.slice(0,20).map(v=>v.slice(0,300)).join('; ')||'Ninguno identificado']]),
 '', '## Texto del correo'+(email.texto_recortado?' (recortado a 16000 caracteres)':''), '',
 String(email.cuerpo||'').split(/\r?\n/).map(line=>'> '+cell(line)).join('\n')
];
return { json: { routing: { tracker_name:result.tipo_ticket, category:result.categoria, user_id:result.assigned_to_id, membership_id:result.membership_id, role_id:result.role_id, reason:result.motivo_asignacion.slice(0,1500) }, issue: { custom_fields: validRequester ? [{ id: 1, value: requesterEmail }] : [], project_id:result.project_id,  subject: ((email.demo ? '[DEMO] ' : '') + (result.requiere_revision ? '[REVISAR] ' : '') + result.resumen.trim()).slice(0,255), description:lines.join('\n'), priority_id: result.requiere_revision ? 2 : priorities[result.prioridad] } } };
