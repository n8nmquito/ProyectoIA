const original = $input.item;
const supported = new Set(['image/png', 'image/jpeg', 'image/webp', 'application/pdf']);
const maxFile = 4 * 1024 * 1024;
const maxTotal = 8 * 1024 * 1024;
const maxFiles = 4;
const selected = {};
const inventory = [];
let total = 0;
for (const [key, file] of Object.entries(original.binary || {})) {
  const mime = String(file.mimeType || 'application/octet-stream').toLowerCase();
  const entry = { archivo: file.fileName || key, tipo: mime, para_ia: false, motivo: 'Formato no seleccionado para IA; se adjunta a Redmine.' };
  if (supported.has(mime)) {
    try {
      const buffer = await this.helpers.getBinaryDataBuffer($itemIndex, key);
      if (buffer.length <= maxFile && total + buffer.length <= maxTotal && Object.keys(selected).length < maxFiles) {
        selected[key] = file;
        total += buffer.length;
        entry.para_ia = true;
        entry.motivo = 'Seleccionado para análisis visual/documental.';
      } else {
        entry.motivo = 'Supera los límites de análisis IA; se adjunta a Redmine.';
      }
    } catch {
      entry.motivo = 'No se pudo preparar para IA; se intentará adjuntar a Redmine.';
    }
  }
  inventory.push(entry);
}
return { json: { ...original.json, adjuntos: inventory }, binary: selected };
