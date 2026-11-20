'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {resolve} = require('node:path');
const dir = resolve(process.argv[2]);
const plan = '6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9';
const admission = {schema_version:'admission.sample.v1-D0',mode:'D0_ADMISSION_STORE_0186',tenant:'synthetic-tenant',company:'synthetic-company',phase:'PENDING',version:0,sample_reserved_minor:0,sample_observed_minor:0,sample_remaining_minor:1000,admission:'DENY',dispatch_allowed:false,spend_allowed:false,release_ready:false,actual_cost_minor:null,authoritative:false};
const office = {schema_version:'office.workbench.v1-D0',mode:'D0_OFFICE_WORKBENCH_0187',tenant:'synthetic-tenant',company:'synthetic-company',world_id:'demo-world',plan_digest:plan,layout_revision:'draft-hybrid-floor-1',iv:'HOLD',release:'HOLD',freshness:'HISTORICAL_SAMPLE',dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,real_run_count:null,geometry_join:'HOLD',sample_event_count:5,roles:['orchestrator','research','engineer','qa'].map((role,i)=>({role,station_id:'station-'+role,observed:i===2?2:1,total:i===2?2:1}))};
const taskBudget = {schema_version:'task.budget.snapshot.v1-D0',mode:'D0_PAIRED_SAMPLE_0188',tenant:'synthetic-tenant',company:'synthetic-company',plan_digest:plan,task_id:'research',run_id:'demo-run',sample_budget_ref:'demo-budget',consistency:'STABLE_DOUBLE_READ_NOT_ATOMIC',freshness:'HISTORICAL_SAMPLE',causality:'UNPROVEN',lease_binding:'HOLD',geometry_join:'HOLD',dispatch_allowed:false,spend_allowed:false,release_ready:false,authoritative:false,pair_id:'a'.repeat(32),workbench_event_seq:5,research_event_seq:3,admission_version:0,sample_admission_ref:null,office,budget:admission};
const outbox = {schema_version:'outbox.review.projection.v1-D0',mode:'D0_OUTBOX_REVIEW_0184',tenant:'synthetic-tenant',company:'synthetic-company',phase:'LOCAL_HOLD',generation:null,readback_recorded:false,admission:'DENY',dispatch_allowed:false,retry_allowed:false,reconciled:false,provider_called:false,release_ready:false};
const specs = [
 {name:'admission',url:'/admission/sample-projection',body:admission,hold:'D0_ADMISSION_READBACK_HOLD'},
 {name:'outbox',url:'/outbox/review-projection',body:outbox,hold:'D0_OUTBOX_READBACK_HOLD'},
 {name:'task-budget',url:'/task-budget/sample-projection',body:taskBudget,hold:'D0_TASK_BUDGET_HOLD'},
];
async function mockRun(GET, handler, {controller, port}={}) {
 const oldFetch = global.fetch, oldTimeout = AbortSignal.timeout;
 const savedPort = process.env.AICOS_D0_BACKEND_PORT;
 const ac = controller || new AbortController();
 try {
  AbortSignal.timeout = () => ac.signal;
  if (port !== undefined) process.env.AICOS_D0_BACKEND_PORT = port;
  else delete process.env.AICOS_D0_BACKEND_PORT;
  global.fetch = handler;
  return await Promise.race([
   GET().then(r => ({status:r.status, response:r}), error => ({status:'REJECTED',error})),
   new Promise(resolve => setTimeout(() => resolve({status:'PENDING_AFTER_ABORT'}),150)),
  ]);
 } finally {
  global.fetch=oldFetch; AbortSignal.timeout=oldTimeout;
  if (savedPort === undefined) delete process.env.AICOS_D0_BACKEND_PORT;
  else process.env.AICOS_D0_BACKEND_PORT=savedPort;
 }
}
for (const s of specs) {
 const {GET} = require(resolve(dir,`app/api/demo/${s.name}/route.js`));
 test(`${s.name}: valid original D0 read remains 200, local-only`,async()=>{
  const r=await mockRun(GET, async(url,opts)=>{
   assert.equal(url,'http://127.0.0.1:8000/demo/v1'+s.url);
   assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');assert.equal(opts.method,'GET');
   return Response.json(s.body);
  });
  assert.equal(r.status,200);assert.equal(r.response.headers.get('cache-control'),'no-store');
  assert.deepEqual(await r.response.json(),s.body);
 });
 test(`${s.name}: authority-bearing contract fails closed`,async()=>{
  const r=await mockRun(GET,async()=>Response.json({...s.body,dispatch_allowed:true}));
  assert.equal(r.status,503);assert.equal((await r.response.json()).mode,s.hold);
 });
 test(`${s.name}: oversized JSON fails closed`,async()=>{
  const r=await mockRun(GET,async()=>Response.json({x:'q'.repeat(12000)}));assert.equal(r.status,503);
 });
 test(`${s.name}: rejected fetch fails closed`,async()=>{
  const r=await mockRun(GET,async()=>{throw Error('offline');});assert.equal(r.status,503);
 });
 test(`${s.name}: late valid response after abort must fail closed`,async()=>{
  const ac=new AbortController();
  const r=await mockRun(GET,async()=>{ac.abort();return Response.json(s.body);},{controller:ac});
  assert.equal(r.status,503,'no 200 from a completed-but-expired request');
 });
 test(`${s.name}: ignored-abort pending fetch must terminate with 503`,async()=>{
  const ac=new AbortController();ac.abort();
  const r=await mockRun(GET,async()=>new Promise(()=>{}),{controller:ac});
  assert.equal(r.status,503,'an abort-ignoring fetch cannot keep the request pending');
 });
 test(`${s.name}: ignored-abort stalled body must terminate with 503`,async()=>{
  const ac=new AbortController();
  const r=await mockRun(GET,async()=>{ac.abort();return new Response(new ReadableStream({start(){}}),{headers:{'content-type':'application/json'}});},{controller:ac});
  assert.equal(r.status,503,'a pending reader.read cannot keep the request pending');
 });
 test(`${s.name}: unresolved body cancel must not delay 503`,async()=>{
  const r=await mockRun(GET,async()=>new Response(new ReadableStream({
   start(c){c.enqueue(new Uint8Array(12000));},cancel(){return new Promise(()=>{});}
  }),{headers:{'content-type':'application/json'}}));
  assert.equal(r.status,503,'unbounded reader.cancel cannot keep the request pending');
 });
 test(`${s.name}: invalid backend port never calls fetch`,async()=>{
  let called=false;
  const r=await mockRun(GET,async()=>{called=true;throw Error('bad');},{port:'17301@evil.test'});
  assert.equal(r.status,503);assert.equal(called,false);
 });
}
