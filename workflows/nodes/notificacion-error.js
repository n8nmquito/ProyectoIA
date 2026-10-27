let email={};try {email=$('Normalizar correo').item.json;}catch {try{email=$('Leer buzón IMAP').item.json;}catch{}}
let raw={};try{raw=$('Leer buzón IMAP').item.json;}catch{}
const sender=String(email.remitente || raw.from?.value?.[0]?.address || raw.from?.text || raw.from || '').trim();
const match=sender.match(/<([^<>]+)>$/);const to=(match?match[1]:sender).trim().toLowerCase();
const headers=raw.headers||raw.metadata||{};
const header=name=>String(Object.entries(headers).find(([key])=>key.toLowerCase()===name)?.[1]||'').toLowerCase();
const valid=/^[a-z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$/i.test(to) && !/[\r\n,;]/.test(to);
const automatic=(header('auto-submitted') && header('auto-submitted')!=='no') || /bulk|list|junk/.test(header('precedence')) || header('list-id') || /^(no[._-]?reply|mailer-daemon|postmaster)@/.test(to);
const reason=!valid?'Remitente no válido':email.demo?'Correo de prueba':to==='n8n.mquito@gmail.com'?'Buzón propio':/@(?:example\.(?:com|org|net|invalid)|[^@]+\.invalid)$/.test(to)?'Dirección de ejemplo':automatic?'Mensaje automático':'';
const asunto=String(email.asunto||raw.subject||'Solicitud de soporte').replace(/[\r\n]/g,' ').slice(0,180);
const kind='error';
let subject,text;
if(kind==='ticket') {subject='[Mquito] Ticket #'+$json.ticket_id+' creado';text='Hola,\n\nRegistramos tu solicitud: '+asunto+'\nTicket: #'+$json.ticket_id+'\nPodés consultar su estado en: '+$json.url+'\n\nMesa de soporte TI - Mquito';}
else if(kind==='omitido') {subject='[Mquito] Correo sin ticket de soporte';text='Hola,\n\nTu correo «'+asunto+'» fue clasificado como contenido ajeno al soporte TI y no se creó un ticket. Si se trata de un problema técnico, enviá una nueva solicitud con el sistema afectado y una descripción del problema.\n\nMesa de soporte TI - Mquito';}
else {subject='[Mquito] No se pudo completar el procesamiento';text='Hola,\n\nNo pudimos completar el procesamiento automático de tu correo «'+asunto+'». El caso quedó registrado en la ejecución para revisión. Antes de reenviar, consultá con soporte si ya existe un ticket para evitar duplicados.\n\nMesa de soporte TI - Mquito';}
return {json:{...$json,notificacion:{enviar:!reason,omision:reason,para:valid?to:'',asunto:subject,texto:text}}};
