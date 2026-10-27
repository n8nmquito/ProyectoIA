// Usage: node classifier/build-workflow.cjs input.json output.json
const fs = require('fs');
const { randomUUID } = require('crypto');
const [input, output, credentialFile] = process.argv.slice(2);
if (!input || !output) throw new Error('Indicar input.json output.json');
const w = JSON.parse(fs.readFileSync(input, 'utf8').replace(/^\uFEFF/, ''));
const inference = fs.readFileSync('classifier/predict.js', 'utf8').split("if (typeof module")[0];
const jsCode = inference + '\n' + fs.readFileSync('classifier/classify-postgres.js','utf8');
function add(name, code, pos, notes) {
  let n = w.nodes.find(n => n.name === name);
  if (!n) { n = {id: randomUUID(), name, type:'n8n-nodes-base.code', typeVersion:2, position:pos}; w.nodes.push(n); }
  n.parameters = {mode:'runOnceForEachItem',jsCode:code}; n.notes = notes; n.notesInFlow = true;
}
add('Clasificar correo - TF-IDF', jsCode, [720,-80], 'Lee el modelo de PostgreSQL, sin coeficientes incrustados. Si falta o es inválido: clasificación no disponible y continúa el agente. Recupera correo y adjuntos originales.');
add('Comparar clasificaciones', fs.readFileSync('workflows/nodes/comparar-clasificaciones.js','utf8'), [1264,224], 'Registra coincidencia, no precisión. El agente no recibe la predicción ML. La categoría final sigue siendo la del agente.');
let pg = w.nodes.find(n=>n.name==='Cargar modelo ML - PostgreSQL');
if (!pg) { pg={id:randomUUID(),name:'Cargar modelo ML - PostgreSQL',type:'n8n-nodes-base.postgres',typeVersion:2.7,position:[448,-80]}; w.nodes.push(pg); }
pg.parameters={operation:'executeQuery',query:'SELECT (SELECT artifact FROM ml.modelos WHERE activo = true LIMIT 1) AS modelo;',options:{queryBatching:'independently',connectionTimeout:5}};
pg.onError='continueRegularOutput';
pg.notes='Cuenta solo lectura. Siempre devuelve una fila (modelo null si no hay activo). Ante error de conexión, continúa al clasificador para recuperar correo y adjuntos. Timeout de conexión: 5 s; consulta: 5 s por rol PostgreSQL.';
pg.notesInFlow=true;
if(credentialFile){const ref=JSON.parse(fs.readFileSync(credentialFile,'utf8').replace(/^\uFEFF/,''));pg.credentials={postgres:{id:ref.id,name:ref.name}};}
function link(a,b) { w.connections[a] ??= {}; w.connections[a].main ??= []; w.connections[a].main[0] = [{node:b,type:'main',index:0}]; }
link('Normalizar correo','Cargar modelo ML - PostgreSQL');
link('Cargar modelo ML - PostgreSQL','Clasificar correo - TF-IDF');
link('Clasificar correo - TF-IDF','Seleccionar adjuntos para IA');
link('Agente IA - Analizar solicitud','Comparar clasificaciones');
link('Comparar clasificaciones','Preparar ticket - Intaco');
// Original error branch, credentials, model choice and activation state are preserved.
fs.writeFileSync(output,JSON.stringify(w,null,2));
console.log('Flujo preparado:',w.nodes.length,'nodos; modelo externo en PostgreSQL');
