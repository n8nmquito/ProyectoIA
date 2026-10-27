const original = $('Normalizar correo').item;
const response = $json;
const classes = ['accesos', 'aplicaciones', 'infraestructura', 'otros'];
const probabilities = response.probabilidades || {};
const valid = response.muestras_entrenamiento === 300
  && response.modelo_version === 'modelo_clasificador_300'
  && classes.includes(response.categoria)
  && Number.isFinite(response.confianza)
  && response.confianza >= 0 && response.confianza <= 1
  && classes.every(c => Number.isFinite(probabilities[c]) && probabilities[c] >= 0 && probabilities[c] <= 1)
  && Math.abs(classes.reduce((s,c) => s + probabilities[c],0) - 1) < 0.000001
  && Math.abs(probabilities[response.categoria] - response.confianza) < 0.000001;
const clasificacion_ml = valid ? {
  ...response, probabilidad: response.confianza,
  almacenamiento: 'API Python: modelo_clasificador_300.pkl',
} : {
  categoria: null, probabilidad: null, probabilidades: {},
  estado: 'clasificacion_no_disponible', modelo_version: null,
  requiere_revision: true, modo: 'comparacion_sin_decidir_ticket',
  motivo: 'La API Python no respondió con una clasificación válida.',
};
return { json: { ...original.json, clasificacion_ml },
  ...(original.binary ? { binary: original.binary } : {}) };
