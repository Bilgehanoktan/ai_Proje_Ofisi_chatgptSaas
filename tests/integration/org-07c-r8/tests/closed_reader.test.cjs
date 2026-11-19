const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createProjectionReader}=require('../build/features/data/projectionRead.js');
const {parseOrganization}=require('../build/features/organization/organizationProjection.js');
const {GET}=require('../build/app/api/demo/organization/route.js');
const scope={tenant_id:'synthetic-tenant',company_id:'synthetic-company',environment_id:'A0_SAMPLE_ONLY'};
const projection={schema:'org.studio.preview.v0-D0',scope,revision:'a'.repeat(64),sequence:1,previous_revision:null,units:[{id:scope.company_id,kind:'company',parent:null}],positions:[],decision:'HOLD',authoritative:false,identity_owner:'HOLD',geometry_join:'HOLD',runtime_binding:null,dispatch_allowed:false};
const route=(url,init)=>{assert.equal(url,'/api/demo/organization');assert.equal(init.credentials,'same-origin');return GET(new Request('http://localhost'+url,init));};
const closed={phase:'hold',data:null,reason:'READBACK_HOLD'};
test('patched central reader -> actual closed GET clears historical data on refresh',async()=>{
 const states=[];let historical=true;
 const reader=createProjectionReader('organization',parseOrganization,s=>states.push(s),(url,init)=>historical?Promise.resolve(Response.json(projection)):route(url,init));
 await reader.read();assert.equal(states.at(-1).phase,'historical');assert.equal(states.at(-1).data.revision,projection.revision);
 historical=false;await reader.read();assert.deepEqual(states.at(-2),{phase:'loading',data:null});assert.deepEqual(states.at(-1),closed);
});
test('late historical response cannot overwrite later real closed GET',async()=>{
 const states=[];let finish;let calls=0;
 const reader=createProjectionReader('organization',parseOrganization,s=>states.push(s),(url,init)=>++calls===1?new Promise(resolve=>finish=resolve):route(url,init));
 const old=reader.read();await reader.read();assert.deepEqual(states.at(-1),closed);
 finish(Response.json(projection));await old;assert.deepEqual(states.at(-1),closed);
});
test('actual closed GET with fresh central reader never publishes historical data',async()=>{
 const states=[];const reader=createProjectionReader('organization',parseOrganization,s=>states.push(s),route);
 await reader.read();assert.deepEqual(states,[{phase:'loading',data:null},closed]);
});
