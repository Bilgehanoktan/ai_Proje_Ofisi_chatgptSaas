const assert=require('node:assert/strict');
const {test}=require('node:test');
const path=require('node:path');
const {parseOrganization,organizationCap}=require(path.join(process.env.ORG07C_JS,'organization/organizationProjection.js'));
const {readOrganizationProxy}=require(path.join(process.env.ORG07C_JS,'organization/organizationProxy.js'));
const {readProjection,createProjectionReader}=require(path.join(process.env.ORG07C_JS,'data/projectionRead.js'));
const port=Number(process.env.ORG07C_PORT),head=process.env.ORG07C_HEAD;
const req=()=>new Request('http://localhost/api/demo/organization');
const cred=async()=> 'opaque-valid';
const proxy=(request=req(),provider=cred,transport=fetch)=>readOrganizationProxy(request,port,provider,transport);
const backend=()=>fetch(`http://127.0.0.1:${port}/demo/v1/organization/studio-preview`,{headers:{Authorization:'Bearer opaque-valid'}}).then(r=>r.json());
const response=(body)=>Response.json(body);
async function denied(p){const r=await p;assert.equal(r.status,503);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),{mode:'D0_ORGANIZATION_READ_HOLD'});}
const browserTransport=async(url,init)=>{assert.equal(url,'/api/demo/organization');assert.equal(init.credentials,'same-origin');assert.equal(init.cache,'no-store');return proxy(new Request('http://localhost'+url,init));};
test('actual loopback R3 SQLite -> proxy -> central reader',async()=>{const v=await readProjection('organization',parseOrganization,new AbortController().signal,browserTransport);assert.equal(v.revision,head);assert.equal(v.positions.length,3);assert.equal(v.units.filter(u=>u.kind==='department').length,2);assert.equal(v.decision,'HOLD');assert.equal(v.runtime_binding,null);assert.equal(v.dispatch_allowed,false);});
test('actual HTTP expired session',async()=>denied(proxy(req(),async()=> 'opaque-expired')));
test('actual HTTP other tenant',async()=>denied(proxy(req(),async()=> 'opaque-other')));
test('actual HTTP unknown credential',async()=>denied(proxy(req(),async()=> 'unknown')));
test('no server context does not call backend',async()=>denied(readOrganizationProxy(req(),port,undefined,()=>{throw Error('must not fetch')})));
test('caller authorization rejected before provider',async()=>denied(proxy(new Request('http://localhost/api/demo/organization',{headers:{Authorization:'Bearer opaque-valid'}}),async()=>{assert.fail('provider called')})));
test('caller scope query rejected',async()=>denied(proxy(new Request('http://localhost/api/demo/organization?tenant=x'))));
test('POST rejected',async()=>denied(proxy(new Request('http://localhost/api/demo/organization',{method:'POST',body:'{}'}))));
test('invalid port rejected',async()=>denied(readOrganizationProxy(req(),65535,cred)));
test('credential provider failure generic',async()=>denied(proxy(req(),async()=>{throw Error('secret')})));
test('backend redirect rejected',async()=>denied(proxy(req(),cred,async()=>Response.redirect('http://localhost/other'))));
test('wrong content type rejected',async()=>denied(proxy(req(),cred,async()=>new Response('{}',{headers:{'Content-Type':'text/plain'}}))));
test('response cap enforced',async()=>denied(proxy(req(),cred,async()=>new Response(' '.repeat(organizationCap+1),{headers:{'Content-Type':'application/json'}}))));
test('bad UTF-8 rejected',async()=>denied(proxy(req(),cred,async()=>new Response(new Uint8Array([0xff]),{headers:{'Content-Type':'application/json'}}))));
test('actual shape accepted and no identity field',async()=>{const v=await backend();assert.ok(parseOrganization(v));assert.ok(!JSON.stringify(v).includes('demo-reader'));assert.ok(!JSON.stringify(v).includes('demo-w'));});
for(const [name,modify] of [
 ['authority',v=>v.authoritative=true],['dispatch',v=>v.dispatch_allowed=true],['runtime binding',v=>v.runtime_binding='demo-run'],['extra identity',v=>v.positions[0].agent_instance_id='demo-leak'],['bad environment',v=>v.scope.environment_id='prod'],['duplicate unit',v=>v.units.push(v.units[0])],['invalid unit parent',v=>v.units.find(u=>u.kind==='department').parent='absent'],['wrong company root',v=>v.scope.company_id='synthetic-other'],['unknown position unit',v=>v.positions[0].unit='absent'],['duplicate position',v=>v.positions.push(v.positions[0])],['reporting cycle',v=>v.positions[0].reports_to=v.positions[0].id],['missing manager',v=>v.positions[0].reports_to='absent'],['reserved role',v=>v.positions[0].role='independent-verifier'],['bad genesis',v=>v.previous_revision='a'.repeat(64)],['unsafe sequence',v=>v.sequence=Number.MAX_SAFE_INTEGER+1],['oversized list',v=>v.units=Array(4097).fill(v.units[0])]]){
 test('parser rejects '+name,async()=>{const v=await backend();modify(v);assert.equal(parseOrganization(v),null);});
}
test('invalid contract rejected at proxy',async()=>{const v=await backend();v.dispatch_allowed=true;await denied(proxy(req(),cred,async()=>response(v)));});
test('central reader clears data on denied refresh',async()=>{let allow=true;const states=[];const r=createProjectionReader('organization',parseOrganization,s=>states.push(s),async(url,init)=>allow?browserTransport(url,init):Response.json({}, {status:503}));await r.read();assert.equal(states.at(-1).phase,'historical');allow=false;await r.read();assert.deepEqual(states.at(-1),{phase:'hold',data:null,reason:'READBACK_HOLD'});});
test('central reader cancels pending stale response',async()=>{let release;const states=[];const r=createProjectionReader('organization',parseOrganization,s=>states.push(s),async()=>new Promise(r=>release=r));const pending=r.read();r.cancel();release(response(await backend()));await pending;assert.equal(states.at(-1).phase,'loading');assert.equal(states.at(-1).data,null);});
test('aborted request fails closed',async()=>{const c=new AbortController();c.abort();await denied(proxy(new Request('http://localhost/api/demo/organization',{signal:c.signal})));});
test('credential provider respects abort before backend',async()=>{const c=new AbortController();let seen;const p=proxy(new Request('http://localhost/api/demo/organization',{signal:c.signal}),async(_r,signal)=>{seen=signal;return new Promise(()=>{});},async()=>{assert.fail('backend called')});await new Promise(r=>setTimeout(r,10));c.abort();await denied(p);assert.ok(seen.aborted);});
test('credential timeout fails closed',async()=>{const start=Date.now();const keep=setTimeout(()=>{},3000);try{await denied(proxy(req(),async()=>new Promise(()=>{})));assert.ok(Date.now()-start<3500);}finally{clearTimeout(keep);}});
test('malformed server token is not forwarded',async()=>denied(proxy(req(),async()=> 'opaque\nsecret',async()=>{assert.fail('backend called')})));
test('SQLite bytes unchanged after all read requests',async()=>{const r=await fetch(`http://127.0.0.1:${port}/test-only/integrity`);assert.deepEqual(await r.json(),{unchanged:true});});
