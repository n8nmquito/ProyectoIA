const assert=require('node:assert/strict');
const fs=require('fs');
const vm=require('node:vm');
const {predict}=require('./predict');
const model=require('./model.json');
for(const f of require('./parity-fixtures.json')) {
  const actual=predict(model,f.text);
  model.classes.forEach((c,i)=>assert.ok(Math.abs(actual.probabilidades[c]-f.probabilities[i])<1e-10, 'Python/JS parity: '+c));
}
assert.equal(predict(model,'🦊 xyzabc').categoria,null);
assert.equal(predict(model,'').estado,'sin_vocabulario_conocido');
if (model.source === 'synthetic') assert.equal(predict(model,'cuenta bloqueada contraseña').categoria,'accesos');
const inputFile=process.argv[2] || 'workflows/correo-ia-redmine.json';
const w=JSON.parse(fs.readFileSync(inputFile,'utf8').replace(/^\uFEFF/,''));
const find=name=>w.nodes.find(n=>n.name===name);
const classify=vm.runInNewContext('(function($json,$){'+find('Clasificar correo - TF-IDF').parameters.jsCode+'})');
const original={json:{asunto:'Cuenta bloqueada',cuerpo:'Mi contraseña expiró',message_id:'a'},binary:{attachment_0:{data:'AA==',fileName:'demo.bin'}}};
const result=classify({modelo:model},()=>({item:original}));
assert.equal(result.binary,original.binary);
assert.equal(result.json.message_id,'a');
assert.equal(result.json.clasificacion_ml.datos_entrenamiento,model.source);
assert.equal(result.json.clasificacion_ml.evaluado,false);
const compare=vm.runInNewContext('(function($json,$){'+find('Comparar clasificaciones').parameters.jsCode+'})');
const proposal={categoria:'infraestructura',descripcion:'Descripción original',assigned_to_id:6,project_id:1};
const merged=compare({output:proposal},name=>({item:result}));
assert.equal(merged.json.comparacion_tecnicas.coinciden,result.json.clasificacion_ml.categoria ? result.json.clasificacion_ml.categoria === proposal.categoria : null);
assert.equal(merged.json.output.assigned_to_id,6);
assert.equal(merged.json.output.categoria,proposal.categoria);
assert.equal(proposal.descripcion,'Descripción original');
const empty=classify({modelo:model},()=>({item:{json:{asunto:'',cuerpo:''}}}));
assert.equal(compare({output:JSON.stringify(proposal)},()=>({item:empty})).json.comparacion_tecnicas.coinciden,null);
assert.equal(w.connections['Agente IA - Analizar solicitud'].main[1][0].node,'Sin análisis IA - Revisión');
assert.ok(!find('Agente IA - Analizar solicitud').parameters.text.includes('clasificacion_ml'));
for (const row of [{modelo:null},{error:'connection failed'},{modelo:{classes:[]}}, {modelo:{...model,weights:[]}}]) {
  const fallback=classify(row,()=>({item:original}));
  assert.equal(fallback.json.clasificacion_ml.categoria,null);
  assert.equal(fallback.json.clasificacion_ml.estado,'clasificacion_no_disponible');
  assert.equal(fallback.binary,original.binary);
  assert.equal(compare({output:proposal},()=>({item:fallback})).json.output.assigned_to_id,6);
}
assert.equal(compare({output:proposal},()=>{throw new Error('Missing optional data')}).json.comparacion_tecnicas.coinciden,null);
assert.equal(find('Cargar modelo ML - PostgreSQL').onError,'continueRegularOutput');
assert.ok(!find('Clasificar correo - TF-IDF').parameters.jsCode.includes(JSON.stringify(model.weights)));
console.log('OK: Python/JS parity, empty/OOV, database fallback, malformed model, attachments, comparison isolation.');
