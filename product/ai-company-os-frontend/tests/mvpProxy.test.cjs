const {test}=require('node:test');
const assert=require('node:assert/strict');
const {GET}=require(process.env.MVP_PROXY_JS);
const sections=Object.fromEntries(['orchestrator','runtime','event_store','model','gateway','tools','verifier','finance'].map(k=>[k,'HOLD']));
const body={schema_version:'mvp.diagnostics.v1-D0',mode:'SYNTHETIC_LOCAL_ONLY',plan_digest:'a'.repeat(64),admission:'DENY',dispatch_allowed:false,release_ready:false,provider_called:false,spend_allowed:false,independent_accepted:false,real_run_count:null,sections,sample_event_rows:0,diagnostic_remaining_minor:0,actual_cost_minor:null,revenue_minor:null};
async function withFetch(fn, check){const saved=global.fetch;global.fetch=fn;try{await check();}finally{global.fetch=saved;}}
test('fixed loopback GET, no cache or redirects',async()=>withFetch(async(url,opts)=>{assert.equal(url,'http://127.0.0.1:8000/demo/v1/mvp/diagnostics');assert.equal(opts.method,'GET');assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');return Response.json(body);},async()=>{const r=await GET();assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),body);}));
test('unsafe response refused',async()=>withFetch(async()=>Response.json({...body,dispatch_allowed:true}),async()=>assert.equal((await GET()).status,503)));
test('network failure held',async()=>withFetch(async()=>{throw Error('network')},async()=>assert.equal((await GET()).status,503)));
test('non-JSON held',async()=>withFetch(async()=>new Response('bad'),async()=>assert.equal((await GET()).status,503)));
test('oversize held',async()=>withFetch(async()=>Response.json({data:'x'.repeat(17000)}),async()=>assert.equal((await GET()).status,503)));
test('real local backend readback',{skip:process.env.MVP_LOOPBACK_TEST!=='1'},async()=>{const r=await GET();assert.equal(r.status,200);const data=await r.json();assert.equal(data.sections.event_store,'SQLITE_MEMORY_READBACK_ONLY');assert.equal(data.sample_event_rows,3);assert.equal(data.dispatch_allowed,false);assert.equal(data.diagnostic_remaining_minor,6900);});
