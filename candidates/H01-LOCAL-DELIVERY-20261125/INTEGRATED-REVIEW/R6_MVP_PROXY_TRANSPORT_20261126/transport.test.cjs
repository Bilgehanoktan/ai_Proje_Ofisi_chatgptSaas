// Scoped D0 transport qualification, not FastAPI, Next build or independent acceptance.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const http=require('node:http');
const {GET}=require('./compiled/app/api/demo/mvp/route.js');
const sections=Object.fromEntries(['orchestrator','runtime','event_store','model','gateway','tools','verifier','finance'].map(k=>[k,'HOLD']));
const body={schema_version:'mvp.diagnostics.v1-D0',mode:'SYNTHETIC_LOCAL_ONLY',plan_digest:'a'.repeat(64),admission:'DENY',dispatch_allowed:false,release_ready:false,provider_called:false,spend_allowed:false,independent_accepted:false,real_run_count:null,sections,sample_event_rows:0,diagnostic_remaining_minor:0,actual_cost_minor:null,revenue_minor:null};
const wire=JSON.stringify(body);
async function withServer(handler, check){
  const old=process.env.AICOS_D0_BACKEND_PORT; const hits=[];
  const server=http.createServer((req,res)=>{hits.push([req.method,req.url]);handler(req,res);});
  let bound=false;
  try{
    for(let port=17301;port<=17320;port++){
      try{await new Promise((resolve,reject)=>{const err=e=>{server.removeListener('listening',listen);reject(e);};const listen=()=>{server.removeListener('error',err);resolve();};server.once('error',err);server.once('listening',listen);server.listen(port,'127.0.0.1');});bound=true;break;}catch(e){if(e.code!=='EADDRINUSE')throw e;}
    }
    assert.ok(bound,'no permitted loopback port');process.env.AICOS_D0_BACKEND_PORT=String(server.address().port);
    await check(hits);
  }finally{if(old===undefined)delete process.env.AICOS_D0_BACKEND_PORT;else process.env.AICOS_D0_BACKEND_PORT=old;if(bound){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}}
}
async function hold(){const r=await GET();assert.equal(r.status,503);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),{mode:'D0_READBACK_HOLD'});}
const path='/demo/v1/mvp/diagnostics';
test('actual loopback HTTP preserves safe wire envelope',async()=>withServer((req,res)=>{assert.equal(req.headers.accept,'application/json');res.writeHead(200,{'content-type':'Application/JSON; charset="UTF-8"'});res.end(wire);},async hits=>{const r=await GET();assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),body);assert.deepEqual(hits,[['GET',path]]);}));
test('actual loopback redirect is not followed',async()=>withServer((req,res)=>{res.writeHead(302,{location:'/unexpected'});res.end();},async hits=>{await hold();assert.deepEqual(hits,[['GET',path]]);}));
test('actual ambiguous duplicate content-type rejected',async()=>withServer((req,res)=>{res.writeHead(200,['Content-Type','application/json','Content-Type','text/plain']);res.end(wire);},async()=>hold()));
test('actual streamed response over cap rejected',async()=>withServer((req,res)=>{res.writeHead(200,{'content-type':'application/json'});res.write(' '.repeat(9000));res.end(' '.repeat(9000)+wire);},async()=>hold()));
test('actual malformed UTF-8 rejected',async()=>withServer((req,res)=>{res.writeHead(200,{'content-type':'application/json'});res.end(Buffer.from([0x7b,0xff,0x7d]));},async()=>hold()));
test('actual stalled response body returns HOLD at shared deadline',async()=>withServer((req,res)=>{res.writeHead(200,{'content-type':'application/json'});res.write('{');},async()=>{const start=performance.now();await hold();const elapsed=performance.now()-start;assert.ok(elapsed>=2000&&elapsed<4000,`elapsed=${elapsed}`);}));
test('actual wire with positive dispatch is rejected',async()=>withServer((req,res)=>{res.writeHead(200,{'content-type':'application/json'});res.end(JSON.stringify({...body,dispatch_allowed:true}));},async()=>hold()));
