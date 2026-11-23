'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {GET}=require('../dist_office/app/api/demo/office-workbench/route.js');
const fixture={
  schema_version:'office.workbench.v1-D0',mode:'D0_OFFICE_WORKBENCH_0187',
  tenant:'synthetic-tenant',company:'synthetic-company',world_id:'demo-world',
  plan_digest:'6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9',
  layout_revision:'draft-hybrid-floor-1',iv:'HOLD',release:'HOLD',freshness:'HISTORICAL_SAMPLE',
  dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,
  real_run_count:null,geometry_join:'HOLD',sample_event_count:0,
  roles:[
    {role:'orchestrator',station_id:'station-orchestrator',observed:0,total:1},
    {role:'research',station_id:'station-research',observed:0,total:1},
    {role:'engineer',station_id:'station-engineer',observed:0,total:2},
    {role:'qa',station_id:'station-qa',observed:0,total:1},
  ],
};
function mock({type='application/json',body=JSON.stringify(fixture),status=200,missing=false}={}){
  const headers=new Headers(); if(!missing)headers.set('content-type',type);
  return new Response(new TextEncoder().encode(body),{status,headers});
}
async function get(options={}){
 const saved=globalThis.fetch;let calls=0;
 globalThis.fetch=async(url,config)=>{
   calls++;assert.equal(url,'http://127.0.0.1:8000/demo/v1/office/workbench-projection');
   assert.equal(config.method,'GET');assert.equal(config.cache,'no-store');
   assert.equal(config.redirect,'error');assert.equal(config.headers.Accept,'application/json');
   return mock(options);
 };
 try{return await GET();}finally{globalThis.fetch=saved;assert.equal(calls,1);}
}
async function expectHold(options){const r=await get(options);assert.equal(r.status,503);assert.equal(r.headers.get('Cache-Control'),'no-store');assert.deepEqual(await r.json(),{mode:'D0_OFFICE_WORKBENCH_HOLD'});}

test('valid office D0 fixture returns 200, no-store',async()=>{
 const r=await get();assert.equal(r.status,200);assert.equal(r.headers.get('Cache-Control'),'no-store');assert.deepEqual(await r.json(),fixture);
});
test('valid upper-case media type and charset returns 200',async()=>{
 const r=await get({type:'Application/JSON; Charset=UTF-8'});assert.equal(r.status,200);
});
test('invalid application/jsonp returns fail-closed 503',async()=>await expectHold({type:'application/jsonp'}));
test('invalid application/json-malformed returns fail-closed 503',async()=>await expectHold({type:'application/json-malformed'}));
test('text/plain returns fail-closed 503',async()=>await expectHold({type:'text/plain'}));
test('missing media type returns fail-closed 503',async()=>await expectHold({missing:true}));
test('upstream HTTP 503 returns fail-closed 503',async()=>await expectHold({status:503}));
test('malformed JSON returns fail-closed 503',async()=>await expectHold({body:'{bad'}));
test('oversized JSON returns fail-closed 503',async()=>await expectHold({body:JSON.stringify({...fixture,pad:'x'.repeat(5000)})}));
test('wrong D0 contract returns fail-closed 503',async()=>await expectHold({body:JSON.stringify({...fixture,tenant:'other-tenant'})}));
