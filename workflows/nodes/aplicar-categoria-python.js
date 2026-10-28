// The normalized API result is authoritative, never the agent's category.
const ml = $('Consultar API - Modelo 300').item.json;
const classes = ['accesos', 'aplicaciones', 'infraestructura', 'otros'];
if (!ml || ml.estado !== 'clasificado' || !classes.includes(ml.categoria)
    || ml.muestras_entrenamiento !== 300
    || ml.modelo_version !== 'modelo_clasificador_300'
    || !Number.isFinite(ml.confianza) || ml.confianza < 0 || ml.confianza > 1
    || typeof ml.requiere_revision !== 'boolean') {
  throw new Error('Python no devolvió una categoría válida. No se crea ticket; revisar la ejecución.');
}
let output = $json.output;
if (typeof output === 'string') output = JSON.parse(output);
if (!output || typeof output !== 'object') throw new Error('Falta el análisis del agente.');
const analysis = { ...output };
const proposedCategory = analysis.categoria;
const agreement = proposedCategory === ml.categoria;
analysis.categoria = ml.categoria;
analysis.requiere_revision = analysis.requiere_revision === true
  || ml.requiere_revision === true || !agreement;
if (!agreement) {
  // Discard routing chosen for a category that Python did not select.
  analysis.assigned_to_id = 0;
  analysis.membership_id = 0;
  analysis.role_id = 0;
  analysis.motivo_asignacion = 'Resolver responsable de la categoría final de Python.';
}
const labels = { accesos: 'Accesos', aplicaciones: 'Aplicaciones', infraestructura: 'Infraestructura', otros: 'Otros' };
analysis.descripcion = String(analysis.descripcion || '').slice(0, 4500)
  + '\n\nCategoría final determinada por Python: ' + labels[ml.categoria]
  + '\nConfianza Python: ' + (ml.confianza * 100).toFixed(2) + ' %'
  + '\nCategoría devuelta por el agente: ' + (labels[proposedCategory] || 'No válida');
return { json: { ...$json, output: analysis, comparacion_tecnicas: {
  categoria_ml: ml.categoria, categoria_llm: proposedCategory,
  categoria_final: ml.categoria, autoridad_categoria: 'python',
  coinciden: agreement, modelo_version: ml.modelo_version,
  datos_entrenamiento: ml.datos_entrenamiento, estado_ml: ml.estado,
  evaluacion_accuracy: false,
  nota: 'Python determina la categoría final. El agente recibe esa categoría; la coincidencia no es una evaluación independiente.',
} } };
