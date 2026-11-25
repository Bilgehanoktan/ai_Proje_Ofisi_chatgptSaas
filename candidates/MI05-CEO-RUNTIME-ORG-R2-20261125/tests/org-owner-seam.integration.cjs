'use strict';
// Test-only synthetic owner seam over localhost; never registers an owner on the product route.
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const http=require('node:http');
const {readOwnerBoundOrganization}=require('../compiled/features/organization/organizationOwnerBinding.js');
const {GET}=require('../compiled/app/api/demo/organization/route.js');
const scope={tenant_id:'synthetic-tenant',company_id:'synthetic-company',environment_id:'A0_SAMPLE_ONLY'};
const revision='a'.repeat(64);
const projection={schema:'org.studio.preview.v0-D0',scope,revision,sequence:1,previous_revision:null,units:[{id:'synthetic-company',kind:'company',parent:null},{id:'synthetic-engineering',kind:'department',parent:'synthetic-company'}],positions:[{id:'synthetic-seat',unit:'synthetic-engineering',role:'engineer',reports_to:null,occupied:true}],decision:'HOLD',authoritative:false,identity_owner:'HOLD',geometry_join:'HOLD',runtime_binding:null,dispatch_allowed:false};
const credential='synthetic-test-token';
const owner=async()=>({credential,scope,revision});
let server,port,calls=0,reply;
before(async()=>{server=http.createServer((req,res)=>{calls++;if(req.url!=='/demo/v1/organization/studio-preview'||req.method!=='GET'||req.headers.authorization!==`Bearer ${credential}`){res.writeHead(403);res.end();return}res.writeHead(200,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(reply));});await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(18735,'127.0.0.1',resolve)});port=server.address().port;assert.ok(port>=1024&&port<=49151,'test port outside existing proxy contract');});
after(async()=>{await new Promise(resolve=>server.close(resolve));});
const request=(init={})=>new Request('http://127.0.0.1/api/demo/organization',init);
const read=()=>readOwnerBoundOrganization(request(),port,owner);
async function held(response){assert.equal(response.status,503);assert.equal(response.headers.get('cache-control'),'no-store');assert.deepEqual(await response.json(),{mode:'D0_ORGANIZATION_READ_HOLD'});}
test('positive exact owner scope and revision crosses real HTTP and preserves all deny boundaries',async()=>{reply=projection;const before=calls,r=await read();assert.equal(r.status,200);assert.equal(calls,before+1);assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(r.headers.get('vary'),'Cookie, Authorization');assert.deepEqual(await r.json(),projection);assert.equal(projection.runtime_binding,null);assert.equal(projection.dispatch_allowed,false)});
test('different tenant with otherwise valid projection cannot cross owner boundary',async()=>{reply={...projection,scope:{...scope,tenant_id:'synthetic-other'}};await held(await read())});
test('different company with otherwise valid projection cannot cross owner boundary',async()=>{reply={...projection,scope:{...scope,company_id:'synthetic-other'},units:[{id:'synthetic-other',kind:'company',parent:null},{id:'synthetic-engineering',kind:'department',parent:'synthetic-other'}]};await held(await read())});
test('different environment with otherwise valid projection cannot cross owner boundary',async()=>{reply={...projection,scope:{...scope,environment_id:'A0_REVIEW_ONLY'}};await held(await read())});
test('different revision with otherwise valid projection cannot cross owner boundary',async()=>{reply={...projection,revision:'b'.repeat(64)};await held(await read())});
test('authority escalation in backend response rejected',async()=>{reply={...projection,authoritative:true,dispatch_allowed:true};await held(await read())});
test('existing product route stays ownerless even when test owner seam is available',async()=>{reply=projection;const before=calls;await held(await GET(request()));assert.equal(calls,before)});
test('client Authorization cannot replace the owner and triggers no network',async()=>{reply=projection;const before=calls;await held(await readOwnerBoundOrganization(request({headers:{Authorization:'Bearer client-token'}}),port,owner));assert.equal(calls,before)});
