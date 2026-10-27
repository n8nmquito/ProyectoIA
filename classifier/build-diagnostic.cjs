// Generate an inactive, side-effect-free server test workflow using saved credentials.
// Usage: node classifier/build-diagnostic.cjs private-current.json private-test.json
const fs=require('fs'),{randomUUID}=require('crypto');
const saved=JSON.parse(fs.readFileSync(process.argv[2],'utf8').replace(/^\uFEFF/,''));
const classify=saved.nodes.find(n=>n.name==='Clasificar correo - TF-IDF');
const basepg=saved.nodes.find(n=>n.name==='Cargar modelo ML - PostgreSQL');
const w={name:'Prueba técnica ML PostgreSQL - temporal',nodes:[],connections:{},settings:{executionOrder:'v1',saveManualExecutions:true}};
function add(name,type,parameters,pos){const n={id:randomUUID(),name,type,typeVersion:type==='n8n-nodes-base.code'?2:1,parameters,position:pos};w.nodes.push(n);return n;}
function link(a,b){w.connections[a]??={main:[[]]};w.connections[a].main[0].push({node:b,type:'main',index:0});}
add('Prueba manual','n8n-nodes-base.manualTrigger',{},[0,0]);
add('Normalizar correo','n8n-nodes-base.code',{jsCode:"return [0,1].map(i=>({json:{asunto:i?'Impresora atascada':'Cuenta bloqueada',cuerpo:i?'La impresora no imprime':'No puedo iniciar sesión con mi contraseña',message_id:'test-'+i},binary:{adjunto:{data:i?'Qg==':'QQ==',mimeType:'text/plain',fileName:'prueba-'+i+'.txt'}}}));"},[200,0]);
link('Prueba manual','Normalizar correo');
for(const [i,query]of [basepg.parameters.query,'SELECT NULL::jsonb AS modelo',"SELECT '{}'::jsonb AS modelo",'SELECT 1/0 AS modelo'].entries()){
  const p=structuredClone(basepg);p.id=randomUUID();p.name='PG caso '+i;p.position=[400,i*250];p.parameters.query=query;w.nodes.push(p);link('Normalizar correo',p.name);
  const c=structuredClone(classify);c.id=randomUUID();c.name='Clasificar caso '+i;c.position=[650,i*250];w.nodes.push(c);link(p.name,c.name);
  const expected=i===0?'clasificado':'clasificacion_no_disponible';
  const test=add('Verificar caso '+i,'n8n-nodes-base.code',{jsCode:`const items=$input.all();if(items.length!==2)throw new Error('Se perdieron correos: '+items.length);for(let i=0;i<2;i++){const x=items[i];if(x.json.message_id!=='test-'+i || x.binary?.adjunto?.fileName!=='prueba-'+i+'.txt')throw new Error('Se mezclaron correos/adjuntos');if(x.json.clasificacion_ml.estado!=='${expected}')throw new Error('Estado inesperado');}return [{json:{caso:${i},correcto:true,correos:items.length}}];`},[900,i*250]);
  link(c.name,test.name);
}
fs.writeFileSync(process.argv[3],JSON.stringify(w));
