// Shared portable inference: used by tests and embedded in the n8n Code node.
function predict(model, text) {
  const start = Date.now();
  const tokens = String(text).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').match(/[a-z0-9]{2,}/g) || [];
  const terms = [...tokens, ...tokens.slice(1).map((t, i) => tokens[i] + ' ' + t)];
  const counts = new Map();
  for (const t of terms) if (Object.hasOwn(model.vocabulary, t)) {
    const i = model.vocabulary[t]; counts.set(i, (counts.get(i) || 0) + 1);
  }
  const features = [...counts].map(([i, count]) => [i, count * model.idf[i]]);
  const norm = Math.sqrt(features.reduce((s, [, v]) => s + v * v, 0));
  const scores = model.weights.map((weights, c) => model.intercept[c] + features.reduce((s, [i, v]) => s + weights[i] * v / norm, 0));
  const exp = scores.map(s => Math.exp(s - Math.max(...scores)));
  const total = exp.reduce((a, b) => a + b, 0);
  const probabilities = exp.map(x => x / total);
  const index = probabilities.indexOf(Math.max(...probabilities));
  return {
    categoria: features.length ? model.classes[index] : null,
    probabilidad: features.length ? probabilities[index] : null,
    probabilidades: Object.fromEntries(model.classes.map((c, i) => [c, probabilities[i]])),
    estado: features.length ? 'clasificado' : 'sin_vocabulario_conocido',
    modelo_version: model.version, datos_entrenamiento: model.source,
    muestras_entrenamiento: model.samples, evaluado: model.evaluated_on_held_out_data,
    modo: 'comparacion_sin_decidir_ticket', tiempo_ms: Date.now() - start,
  };
}
if (typeof module !== 'undefined') module.exports = { predict };
