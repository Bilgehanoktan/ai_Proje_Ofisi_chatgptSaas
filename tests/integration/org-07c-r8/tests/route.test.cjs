const {test}=require('node:test');
const assert=require('node:assert/strict');
const {GET,dynamic}=require('../build/app/api/demo/organization/route.js');
const url='http://localhost/api/demo/organization';
async function closed(request,port){
 const saved=process.env.AICOS_D0_BACKEND_PORT,oldFetch=globalThis.fetch;
 let calls=0;globalThis.fetch=async()=>{calls++;throw Error('unexpected fetch');};
 try{
  if(port===undefined)delete process.env.AICOS_D0_BACKEND_PORT;else process.env.AICOS_D0_BACKEND_PORT=port;
  const r=await GET(request);
  assert.equal(r.status,503);assert.equal(r.headers.get('cache-control'),'no-store');
  assert.deepEqual(await r.json(),{mode:'D0_ORGANIZATION_READ_HOLD'});assert.equal(calls,0);
 }finally{globalThis.fetch=oldFetch;if(saved===undefined)delete process.env.AICOS_D0_BACKEND_PORT;else process.env.AICOS_D0_BACKEND_PORT=saved;}
}
test('default route is dynamic and closed without owner',async()=>{assert.equal(dynamic,'force-dynamic');await closed(new Request(url));});
test('valid configured port does not activate route',async()=>closed(new Request(url),'18000'));
test('bad configured port stays closed',async()=>closed(new Request(url),'65535'));
test('browser cookie cannot activate route',async()=>closed(new Request(url,{headers:{Cookie:'session=demo'}})));
test('browser authorization cannot activate route',async()=>closed(new Request(url,{headers:{Authorization:'Bearer demo'}})));
test('browser scope query cannot activate route',async()=>closed(new Request(url+'?tenant=synthetic-other')));
test('aborted request stays closed',async()=>{const c=new AbortController();c.abort();await closed(new Request(url,{signal:c.signal}));});
test('untrusted forwarded headers cannot activate route',async()=>closed(new Request(url,{headers:{'x-forwarded-host':'remote.example','x-tenant-id':'synthetic-tenant'}})));
