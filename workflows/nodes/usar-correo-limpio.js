// No fallback to the original text if the Python cleaning service fails.
const original = $('Normalizar correo').item;
const cleaned = $json;
if (typeof cleaned.titulo !== 'string' || !cleaned.titulo.trim()
    || typeof cleaned.cuerpo !== 'string' || !cleaned.cuerpo.trim()
    || cleaned.limpieza?.version !== 1
    || typeof cleaned.limpieza.firma_eliminada !== 'boolean'
    || !cleaned.limpieza.datos_redactados
    || typeof cleaned.limpieza.datos_redactados !== 'object') {
  throw new Error('Python no devolvió un correo limpio válido. No se envía el texto original al clasificador ni al agente.');
}
return { json: { ...original.json,
  asunto: cleaned.titulo, cuerpo: cleaned.cuerpo, limpieza: cleaned.limpieza,
}, ...(original.binary ? { binary: original.binary } : {}) };
