const original = $('Normalizar correo').item;
const selection = $('Seleccionar adjuntos para IA').item.json;
const issue = { ...$json.issue };
const inventory = selection.adjuntos || [];
const cell = value => String(value ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\|/g,'&#124;').replace(/[\r\n]+/g,' ');
if (inventory.length) {
 issue.description += '\n\n## Archivos del correo\n\n| Archivo | Tipo | Tratamiento |\n| --- | --- | --- |\n' + inventory.map(a=>'| '+cell(a.archivo)+' | '+cell(a.tipo)+' | '+cell(a.motivo)+' |').join('\n') + '\n\nLos archivos se adjuntan al ticket. La selección para IA no garantiza su lectura; consultar el análisis anterior.';
}
return {json:{issue},binary:original.binary||{}};
