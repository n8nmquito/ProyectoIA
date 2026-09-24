const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'correo-ia-redmine.json'), 'utf8'));
const nodes = Object.fromEntries(wf.nodes.map(n => [n.name, n]));
const file = (name, mime, size = 10) => ({ fileName: name, mimeType: mime, data: Buffer.alloc(size).toString('base64') });
async function run(name, items, links = {}) {
  const context = {
    $json: items[0]?.json, $itemIndex: 0, Buffer,
    $input: { item: items[0], all: () => items },
    $: n => links[n],
    _ctx: { helpers: { getBinaryDataBuffer: async (index, key) => Buffer.from(items[index].binary[key].data, 'base64') } },
  };
  return await vm.runInNewContext('(async function(){' + nodes[name].parameters.jsCode + '\n}).call(_ctx)', context, { timeout: 2000 });
}

(async () => {
  const original = { json: { asunto: 'Prueba', cuerpo: 'Ayuda' }, binary: {
    image: file('captura.png', 'image/png'),
    pdf: file('detalle.pdf', 'application/pdf'),
    text: file('nota.txt', 'text/plain'),
    large: file('grande.pdf', 'application/pdf', 4 * 1024 * 1024 + 1),
  } };
  const selected = await run('Seleccionar adjuntos para IA', [original]);
  assert.equal(Object.keys(selected.binary).join(','), 'image,pdf');
  assert.equal(selected.json.adjuntos.length, 4);
  assert.equal(Object.keys(original.binary).length, 4);
  const limited = await run('Seleccionar adjuntos para IA', [{ json: {}, binary: {
    a: file('a.pdf', 'application/pdf', 4 * 1024 * 1024),
    b: file('b.pdf', 'application/pdf', 4 * 1024 * 1024),
    c: file('c.pdf', 'application/pdf', 1),
  } }]);
  assert.equal(Object.keys(limited.binary).length, 2);
  const five = Object.fromEntries(Array.from({ length: 5 }, (_, i) => [String(i), file(i + '.png', 'image/png')]));
  assert.equal(Object.keys((await run('Seleccionar adjuntos para IA', [{ json: {}, binary: five }])).binary).length, 4);
  const onlyFiles = await run('Normalizar correo', [{ json: { subject: 'Solo adjuntos' }, binary: original.binary }]);
  assert.match(onlyFiles.json.cuerpo, /sin texto/);
  assert.equal(Object.keys(onlyFiles.binary).length, 4);
  const fallback = await run('Sin análisis IA - Revisión', [{ json: { error: 'PDF corrupto' } }], { 'Normalizar correo': { item: original } });
  assert.equal(fallback.json.output.requiere_revision, true);
  assert.equal(fallback.json.output.prioridad, 'normal');
  const restored = await run('Recuperar adjuntos originales', [{ json: { issue: { subject: 'Uno', description: 'Descripción' } } }], {
    'Normalizar correo': { item: original }, 'Seleccionar adjuntos para IA': { item: selected },
  });
  assert.equal(Object.keys(restored.binary).length, 4);

  // Dos correos en el mismo lote: no mezclar tokens ni crear un ticket por archivo.
  const split = await run('Separar adjuntos', [
    { json: { issue: { subject: 'Uno' } }, binary: { a: file('../uno.pdf', 'application/pdf'), b: file('dos.txt', 'text/plain') } },
    { json: { issue: { subject: 'Dos' } }, binary: { c: file('tres.png', 'image/png') } },
  ]);
  assert.equal(split.length, 3);
  assert.equal(split[0].json.filename.includes('/'), false);
  const linked = { 'Separar adjuntos': { itemMatching: index => split[index] } };
  const uploads = split.map((_, i) => ({ json: { upload: { token: 'token-' + i } } }));
  const grouped = await run('Reunir tokens de adjuntos', uploads, linked);
  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].json.issue.uploads.length, 2);
  assert.equal(grouped[1].json.issue.uploads[0].token, 'token-2');
  await assert.rejects(run('Reunir tokens de adjuntos', [{ json: {} }], linked), /no devolvió el token/);
  await assert.rejects(run('Reunir tokens de adjuntos', [uploads[0]], linked), /Faltan adjuntos/);
  assert.equal(nodes['Agente IA - Analizar solicitud'].onError, 'continueErrorOutput');
  assert.equal(nodes['Subir adjunto a Redmine'].parameters.genericAuthType, 'httpHeaderAuth');
  assert.equal(wf.active, false);
  console.log('OK: selección y límites IA, preservación, correo sin texto, respaldo y agrupación de adjuntos por ticket.');
})().catch(error => { console.error(error); process.exit(1); });
