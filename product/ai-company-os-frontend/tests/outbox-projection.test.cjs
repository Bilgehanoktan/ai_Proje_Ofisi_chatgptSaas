const assert=require('node:assert/strict');
const {test}=require('node:test');
const {parseOutboxProjection:parse}=require(process.argv[2]);
const {GET}=require(process.argv[3]);
const sample={schema_version:'outbox.review.projection.v1-D0',mode:'D0_OUTBOX_REVIEW_0184',tenant:'synthetic-tenant',company:'synthetic-company',phase:'LOCAL_HOLD',generation:null,readback_recorded:false,admission:'DENY',dispatch_allowed:false,retry_allowed:false,reconciled:false,provider_called:false,release_ready:false};
test('valid phases',()=>{assert.ok(parse(sample));for(const p of ['CLAIMED','UNKNOWN_HOLD','READBACK_HOLD'])assert.ok(parse({...sample,phase:p,generation:1,readback_recorded:p==='READBACK_HOLD'}));});
test('authority flags rejected',()=>{for(const k of ['dispatch_allowed','retry_allowed','reconciled','provider_called','release_ready'])assert.equal(parse({...sample,[k]:true}),null);});
test('scope and extra fields',()=>{assert.equal(parse({...sample,tenant:'other'}),null);assert.equal(parse({...sample,readback_sha:'a'.repeat(64)}),null);});
test('state consistency',()=>{assert.equal(parse({...sample,phase:'UNKNOWN_HOLD'}),null);assert.equal(parse({...sample,phase:'CLAIMED',generation:0}),null);assert.equal(parse({...sample,phase:'READBACK_HOLD',generation:1}),null);});
async function mocked(fn,check){const old=global.fetch;global.fetch=fn;try{await check(await GET());}finally{global.fetch=old;}}
test('proxy fixed loopback only',async()=>mocked(async(url,opts)=>{assert.equal(url,'http://127.0.0.1:8000/demo/v1/outbox/review-projection');assert.equal(opts.redirect,'error');assert.equal(opts.method,'GET');return Response.json(sample);},async r=>{assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),sample);}));
test('proxy fails closed for wrong contract',async()=>mocked(async()=>Response.json({...sample,retry_allowed:true}),async r=>{assert.equal(r.status,503);assert.equal((await r.json()).mode,'D0_OUTBOX_READBACK_HOLD');}));
test('proxy rejects oversized body',async()=>mocked(async()=>Response.json({oversized:'a'.repeat(5000)}),async r=>assert.equal(r.status,503)));
test('proxy failure is HOLD',async()=>mocked(async()=>{throw Error('down');},async r=>assert.equal(r.status,503)));
