let ml = { categoria:null, probabilidad:null, modelo_version:null, datos_entrenamiento:null, estado:'clasificacion_no_disponible' };
try { ml = { ...ml, ...$('Clasificar correo - TF-IDF').item.json.clasificacion_ml }; } catch { /* Optional comparison must not block the ticket. */ }
let output = $json.output;
if (typeof output === 'string') output = JSON.parse(output);
if (!output || typeof output !== 'object') throw new Error('Falta resultado del agente para comparar');
const analysis = { ...output };
const comparison = {
  categoria_ml: ml.categoria, categoria_llm: analysis.categoria,
  coinciden: ml.categoria ? ml.categoria === analysis.categoria : null,
  modelo_version: ml.modelo_version, datos_entrenamiento: ml.datos_entrenamiento,
  estado_ml: ml.estado,
  evaluacion_accuracy: false,
  nota: 'Comparación operativa, no evaluación de precisión: falta etiqueta humana y el agente puede utilizar adjuntos y herramientas.',
};
const labels = { accesos: 'Accesos', aplicaciones: 'Aplicaciones', infraestructura: 'Infraestructura', otros: 'Otros' };
analysis.descripcion = String(analysis.descripcion || '').slice(0,4800)
  + '\n\nTF-IDF + regresión logística: ' + (labels[ml.categoria] || 'Sin clasificación');
return { json: { ...$json, output: analysis, comparacion_tecnicas: comparison } };
