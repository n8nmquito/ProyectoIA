// Input comes from the Postgres node; recover the linked email and binary originals.
const input = $('Normalizar correo').item;
let clasificacion_ml;
try {
  const model = $json.modelo;
  if (!model || typeof model !== 'object') throw new Error('Modelo no disponible');
  const categories = ['accesos','aplicaciones','infraestructura','otros'];
  if (!Array.isArray(model.classes) || model.classes.length !== 4 || new Set(model.classes).size !== 4 || !model.classes.every(c=>categories.includes(c))) throw new Error('Categorías inválidas');
  if (!Array.isArray(model.idf) || !model.idf.length || !model.idf.every(Number.isFinite)) throw new Error('IDF inválido');
  if (!model.vocabulary || typeof model.vocabulary !== 'object' || !Object.values(model.vocabulary).every(i=>Number.isInteger(i) && i>=0 && i<model.idf.length)) throw new Error('Vocabulario inválido');
  if (!Array.isArray(model.weights) || model.weights.length!==4 || !model.weights.every(w=>Array.isArray(w) && w.length===model.idf.length && w.every(Number.isFinite))) throw new Error('Coeficientes inválidos');
  if (!Array.isArray(model.intercept) || model.intercept.length!==4 || !model.intercept.every(Number.isFinite)) throw new Error('Interceptos inválidos');
  const text = String(input.json.asunto || '').slice(0,255) + '\n' + String(input.json.cuerpo || '').slice(0,16000);
  clasificacion_ml = predict(model, text);
  if (!Object.values(clasificacion_ml.probabilidades).every(Number.isFinite)) throw new Error('Resultado no finito');
  clasificacion_ml.almacenamiento = 'PostgreSQL: n8n.ml.modelos';
} catch {
  clasificacion_ml = {
    categoria: null, probabilidad: null, probabilidades: {},
    estado: 'clasificacion_no_disponible', modelo_version: null,
    datos_entrenamiento: null, evaluado: false,
    modo: 'comparacion_sin_decidir_ticket',
    motivo: 'No se pudo cargar o procesar el modelo; continúa el agente principal.',
  };
}
return { json: { ...input.json, clasificacion_ml }, ...(input.binary ? { binary: input.binary } : {}) };
