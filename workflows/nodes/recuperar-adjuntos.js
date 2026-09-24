// Los originales se recuperan antes de la selección para IA, sin perder archivos.
const original = $('Normalizar correo').item;
const selection = $('Seleccionar adjuntos para IA').item.json;
const issue = { ...$json.issue };
const inventory = selection.adjuntos || [];
if (inventory.length) {
  const details = inventory.map(a => '- ' + a.archivo + ' [' + a.tipo + ']: ' + a.motivo).join('\n');
  issue.description += '\n\nARCHIVOS DEL CORREO\n' + details +
    '\nLa selección para IA no garantiza lectura: revisar el análisis o aviso de fallo anterior. Todos los archivos se cargarán en Redmine.';
}
return { json: { issue }, binary: original.binary || {} };
