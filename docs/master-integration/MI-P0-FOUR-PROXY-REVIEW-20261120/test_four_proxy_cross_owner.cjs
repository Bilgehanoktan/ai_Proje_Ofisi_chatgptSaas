'use strict';
const assert=require('node:assert/strict');
const {test}=require('node:test');
const path=require('node:path');
const base=path.resolve(process.argv[2]);
const plan='6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9';
const admission={schema_version:'admission.sample.v1-D0',mode:'D0_ADMISSION_STORE_0186',tenant:'synthetic-tenant',company:'synthetic-company',phase:'PENDING',version:0,sample_reserved_minor:0,sample_observed_minor:0,sample_remaining_minor:1000,admission:'DENY',dispatch_allowed:false,spend_allowed:false,release_ready:false,actual_cost_minor:null,authoritative:false};
const office={schema_version:'office.workbench.v1-D0',mode:'D0_OFFICE_WORKBENCH_0187',tenant:'synthetic-tenant',company:'synthetic-company',world_id:'demo-world',plan_digest:plan,layout_revision:'draft-hybrid-floor-1',iv:'HOLD',release:'HOLD',freshness:'HISTORICAL_SAMPLE',dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,real_run_count:null,geometry_join:'HOLD',sample_event_count:5,roles:['orchestrator','research','engineer','qa'].map((role,i)=>({role,station_id:'station-'+role,observed:i===2?2:1,total:i===2?2:1}))};
const taskBudget={schema_version:'task.budget.snapshot.v1-D0',mode:'D0_PAIRED_SAMPLE_0188',tenant:'synthetic-tenant',company:'synthetic-company',plan_digest:plan,task_id:'research',run_id:'demo-run',sample_budget_ref:'demo-budget',consistency:'STABLE_DOUBLE_READ_NOT_ATOMIC',freshness:'HISTORICAL_SAMPLE',causality:'UNPROVEN',lease_binding:'HOLD',geometry_join:'HOLD',dispatch_allowed:false,spend_allowed:false,release_ready:false,authoritative:false,pair_id:'a'.repeat(32),workbench_event_seq:5,research_event_seq:3,admission_version:0,sample_admission_ref:null,office,budget:admission};
const outbox={schema_version:'outbox.review.projection.v1-D0',mode:'D0_OUTBOX_REVIEW_0184',tenant:'synthetic-tenant',company:'synthetic-company',phase:'LOCAL_HOLD',generation:null,readback_recorded:false,admission:'DENY',dispatch_allowed:false,retry_allowed:false,reconciled:false,provider_called:false,release_ready:false};
const specs=[
 {id:'admission',endpoint:'/demo/v1/admission/sample-projection',hold:'D0_ADMISSION_READBACK_HOLD',body:admission},
 {id:'outbox',endpoint:'/demo/v1/outbox/review-projection',hold:'D0_OUTBOX_READBACK_HOLD',body:outbox},
 {id:'task-budget',endpoint:'/demo/v1/task-budget/sample-projection',hold:'D0_TASK_BUDGET_HOLD',body:taskBudget},
 {id:'office-workbench',endpoint:'/demo/v1/office/workbench-projection',hold:'D0_OFFICE_WORKBENCH_HOLD',body:office},
];
for(const s of specs)s.GET=require(path.resolve(base,'app/api/demo',s.id,'route.js')).GET;
async function withPatch(fetchImpl,go,opts={}){
 const prevFetch=global.fetch,prevTimeout=AbortSignal.timeout,prevPort=process.env.AICOS_D0_BACKEND_PORT;
 const controllers=[];
 try{
   AbortSignal.timeout=ms=>{assert.equal(ms,2500);let c=new AbortController();controllers.push(c);if(opts.preaborted)c.abort();return c.signal;};
   global.fetch=fetchImpl;
   if(opts.port===undefined)delete process.env.AICOS_D0_BACKEND_PORT;else process.env.AICOS_D0_BACKEND_PORT=opts.port;
   return await go(controllers);
 }finally{
   global.fetch=prevFetch;AbortSignal.timeout=prevTimeout;
   if(prevPort===undefined)delete process.env.AICOS_D0_BACKEND_PORT;else process.env.AICOS_D0_BACKEND_PORT=prevPort;
 }
}
function select(url,opts){
 assert.equal(opts.method,'GET');assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');
 assert.equal(opts.headers.Accept,'application/json');
 const s=specs.find(x=>url==='http://127.0.0.1:8000'+x.endpoint);
 assert.ok(s,`unexpected endpoint ${url}`);return s;
}

test('all four pinned proxy GET routes share the exact loopback contract without response cross-talk',async()=>{
 let seen=[];
 await withPatch(async(url,opts)=>{const s=select(url,opts);seen.push(s.id);return Response.json(s.body);},async c=>{
   for(const s of specs){const r=await s.GET();assert.equal(r.status,200,s.id);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),s.body);}
   assert.equal(c.length,4);
 });
 assert.deepEqual(seen,specs.map(s=>s.id));
});

test('one invalid tenant is rejected while other three independent projections remain valid',async()=>{
 await withPatch(async(url,opts)=>{const s=select(url,opts);return Response.json(s.id==='outbox'?{...s.body,tenant:'foreign-tenant'}:s.body);},async()=>{
   const results=await Promise.all(specs.map(s=>s.GET()));
   assert.deepEqual(results.map(r=>r.status),[200,503,200,200]);
   assert.deepEqual(await results[1].json(),{mode:specs[1].hold});
 });
});

test('one indefinitely stalled outbox transport is canceled logically without blocking three concurrent GETs',async()=>{
 await withPatch(async(url,opts)=>{const s=select(url,opts);return s.id==='outbox'?new Promise(()=>{}):Response.json(s.body);},async controllers=>{
   const promise=Promise.all(specs.map(s=>s.GET()));
   assert.equal(controllers.length,4);
   controllers[1].abort();
   const result=await Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(Error('cross-owner stalled')),350))]);
   assert.deepEqual(result.map(x=>x.status),[200,503,200,200]);
   assert.deepEqual(await result[1].json(),{mode:specs[1].hold});
 });
});

test('pre-aborted signals fail closed on every route independently',async()=>{
 await withPatch(async(url,opts)=>{const s=select(url,opts);return Response.json(s.body);},async controllers=>{
   const result=await Promise.all(specs.map(s=>s.GET()));
   assert.deepEqual(result.map(x=>x.status),[503,503,503,503]);
   assert.ok(controllers.every(x=>x.signal.aborted));
 },{preaborted:true});
});

test('invalid backend port fails closed across all four routes with zero calls to fetch',async()=>{
 let calls=0;
 await withPatch(async()=>{calls++;throw Error('network unexpectedly touched');},async()=>{
   const results=await Promise.all(specs.map(s=>s.GET()));
   assert.deepEqual(results.map(x=>x.status),[503,503,503,503]);
 },{port:'17301@evil.test'});
 assert.equal(calls,0);
});

test('Office body cannot be substituted for the other three D0 read models',async()=>{
 await withPatch(async()=>Response.json(office),async()=>{
   const results=await Promise.all(specs.map(s=>s.GET()));
   assert.deepEqual(results.map(x=>x.status),[503,503,503,200]);
 });
});

test('real native AbortSignal.timeout closes stalled office pipeline by deadline, without a live backend',async()=>{
 const previous=AbortSignal.timeout,prevFetch=global.fetch;
 try{
   AbortSignal.timeout=previous;
   global.fetch=async()=>new Promise(()=>{});
   const start=Date.now();
   const result=await Promise.race([specs[3].GET(),new Promise((_,reject)=>setTimeout(()=>reject(Error('native deadline exceeded 3.5s')),3500))]);
   const elapsed=Date.now()-start;
   assert.equal(result.status,503);assert.ok(elapsed>=2450&&elapsed<3500,`native elapsed ${elapsed}`);
 }finally{AbortSignal.timeout=previous;global.fetch=prevFetch;}
});
