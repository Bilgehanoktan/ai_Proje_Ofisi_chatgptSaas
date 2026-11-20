'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {GET}=require(process.argv[2]);
const payload=(n=5)=>({
 schema_version:'office.workbench.v1-D0',mode:'D0_OFFICE_WORKBENCH_0187',tenant:'synthetic-tenant',company:'synthetic-company',world_id:'demo-world',
 plan_digest:'6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9',layout_revision:'draft-hybrid-floor-1',
 sample_event_count:n,roles:[
 {role:'orchestrator',station_id:'station-orchestrator',observed:Number(n>=1),total:1},
 {role:'research',station_id:'station-research',observed:Number(n>=3),total:1},
 {role:'engineer',station_id:'station-engineer',observed:Number(n>=2)+Number(n>=4),total:2},
 {role:'qa',station_id:'station-qa',observed:Number(n>=5),total:1}],
 iv:'HOLD',release:'HOLD',freshness:'HISTORICAL_SAMPLE',dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,real_run_count:null,geometry_join:'HOLD'});
async function withMock(impl,fn){const oldFetch=global.fetch;global.fetch=impl;try{return await fn()}finally{global.fetch=oldFetch}}
async function withAbortSignal(make,fn){const old=AbortSignal.timeout;AbortSignal.timeout=make;try{return await fn()}finally{AbortSignal.timeout=old}}
test('normal fixed response remains accepted',()=>withMock(async(u,o)=>{assert.equal(o.cache,'no-store');return Response.json(payload())},async()=>{const r=await GET();assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store')}));
test('aborted signal before mock fetch completes must HOLD',()=>withAbortSignal(()=>{const c=new AbortController();c.abort();return c.signal},()=>withMock(async()=>Response.json(payload()),async()=>{const r=await GET();assert.equal(r.status,503)})));
test('transport abort while returning valid body must HOLD',()=>{const c=new AbortController();return withAbortSignal(()=>c.signal,()=>withMock(async()=>{c.abort();return Response.json(payload())},async()=>{const r=await GET();assert.equal(r.status,503)}))});
test('invalid scope must HOLD',()=>withMock(async()=>Response.json({...payload(),tenant:'evil'}),async()=>{assert.equal((await GET()).status,503)}));
test('oversize must HOLD',()=>withMock(async()=>Response.json({x:'a'.repeat(5000)}),async()=>{assert.equal((await GET()).status,503)}));
test('transport error must HOLD',()=>withMock(async()=>{throw Error('offline')},async()=>{assert.equal((await GET()).status,503)}));


// Follow-up PR #23: abort must bound every await, not only a completed response.
async function promptHold(fn){
 let watchdog;
 try{
  const result=await Promise.race([fn(),new Promise((_,reject)=>{watchdog=setTimeout(()=>reject(Error('deadline did not settle')),200)})]);
  assert.equal(result.status,503);
 }finally{clearTimeout(watchdog)}
}

test('abort while fetch promise is pending must HOLD without awaiting transport',()=>{
 const c=new AbortController();let called=0;
 return withAbortSignal(()=>c.signal,()=>withMock(async()=>{
  called++;queueMicrotask(()=>c.abort());return new Promise(()=>{});
 },async()=>{
  await promptHold(()=>GET());assert.equal(called,1);
 }));
});

test('abort while response reader.read is stalled must HOLD promptly',()=>{
 const c=new AbortController();let reads=0;
 return withAbortSignal(()=>c.signal,()=>withMock(async()=>new Response(new ReadableStream({
  pull(){reads++;queueMicrotask(()=>c.abort());return new Promise(()=>{});}
 }),{headers:{'content-type':'application/json'}}),async()=>{
  await promptHold(()=>GET());assert.ok(reads>=1);
 }));
});

test('abort during never-resolving reader.cancel must HOLD promptly',()=>{
 const c=new AbortController();let cancels=0;
 return withAbortSignal(()=>c.signal,()=>withMock(async()=>new Response(new ReadableStream({
  start(s){s.enqueue(new Uint8Array(5000));},
  cancel(){cancels++;queueMicrotask(()=>c.abort());return new Promise(()=>{});}
 }),{headers:{'content-type':'application/json'}}),async()=>{
  await promptHold(()=>GET());assert.equal(cancels,1);
 }));
});
