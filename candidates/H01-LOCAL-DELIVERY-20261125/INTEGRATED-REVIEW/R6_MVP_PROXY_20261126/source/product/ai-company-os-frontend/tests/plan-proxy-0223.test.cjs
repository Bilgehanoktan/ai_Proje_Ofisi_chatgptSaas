const test=require('node:test'),assert=require('node:assert/strict');
const {createServer}=require('node:http'),{readFileSync}=require('node:fs'),{join}=require('node:path');
const {GET}=require(join(process.env.AICOS_STUDIO_OUT,'app/api/demo/plan/route.js'));
const actual=JSON.parse(readFileSync(process.env.AICOS_COMPILED_PLAN,'utf8'));
let server,port,reply,requestPath;
const close=s=>new Promise(resolve=>s.close(resolve));
test.before(async()=>{
 for(let p=18423;p<18453;p++){
  const s=createServer((req,res)=>{requestPath=req.url;reply(req,res);});
  try{await new Promise((resolve,reject)=>{s.once('error',reject);s.listen(p,'127.0.0.1',resolve)});server=s;port=p;break;}catch(e){if(e.code!=='EADDRINUSE')throw e;}
 }
 assert.ok(server);process.env.AICOS_D0_BACKEND_PORT=String(port);
});
test.after(async()=>{delete process.env.AICOS_D0_BACKEND_PORT;if(server)await close(server);});
const respond=(body,status=200,type='application/json')=>(_req,res)=>{res.writeHead(status,{'Content-Type':type});res.end(body);};
test('actual Python compiler output through real HTTP proxy',async()=>{reply=respond(JSON.stringify(actual));const r=await GET();assert.equal(requestPath,'/demo/v1/core/plan-projection');assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),actual)});
for(const [name,body,status,type] of [
 ['upstream 503','{}',503,'application/json'],['invalid media','{}',200,'text/plain'],['invalid JSON','{',200,'application/json'],
 ['injected authority',JSON.stringify({...actual,dispatch_allowed:true}),200,'application/json'],['oversize','x'.repeat(16385),200,'application/json'],['invalid UTF8',Buffer.from([255]),200,'application/json']
])test(name+' returns HOLD',async()=>{reply=respond(body,status,type);const r=await GET();assert.equal(r.status,503);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),{mode:'D0_PLAN_READBACK_HOLD'})});
test('redirect is rejected',async()=>{reply=(_req,res)=>{res.writeHead(302,{Location:'/redirected'});res.end()};assert.equal((await GET()).status,503);assert.equal(requestPath,'/demo/v1/core/plan-projection')});
