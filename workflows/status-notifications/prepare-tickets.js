// Validate the entire paginated response before updating PostgreSQL.
const rows=[]; const seen=new Set();
for(const item of $input.all()) {
 const page=item.json;
 if(!Array.isArray(page.issues)) throw new Error('Redmine no devolvió una página válida de tickets. No se actualizó el seguimiento.');
 for(const issue of page.issues) {
  if(!Number.isSafeInteger(issue.id)||!Number.isSafeInteger(issue.status?.id)||!issue.status.name||!issue.updated_on||!Number.isFinite(Date.parse(issue.updated_on)))throw new Error('Ticket con estado o fecha inválidos.');
  if(seen.has(issue.id))continue; seen.add(issue.id);
  const field=(issue.custom_fields||[]).find(f=>f.id===1 && f.name==='Correo del solicitante');
  const email=typeof field?.value==='string'?field.value.trim():'';
  const valid=email.length<=254 && /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/.test(email);
  const blocked= /@(?:example\.(?:com|net|org)|[^@]*\.invalid)$|@localhost$/i.test(email) || email.toLowerCase()==='n8n.mquito@gmail.com' || /^(no[._-]?reply|mailer-daemon|postmaster)@/i.test(email);
  rows.push({ticket_id:issue.id,status_id:issue.status.id,status_name:issue.status.name,subject:issue.subject||'(Sin asunto)',updated_on:issue.updated_on,
   email,email_valid:valid&&!blocked,email_reason:!valid?'Correo del solicitante vacío o con formato inválido':blocked?'Dirección de ejemplo, automática o del propio buzón':null,
   url:'http://185.208.207.203:3000/issues/'+issue.id});
 }
}
return [{json:{tickets:rows}}];
