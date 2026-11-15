const assert=require('node:assert/strict');
const {test}=require('node:test');
const {parseAdmissionProjection:parse}=require(process.argv[2]);
const {GET}=require(process.argv[3]);
const base={schema_version:'admission.sample.v1-D0',mode:'D0_ADMISSION_STORE_0186',tenant:'synthetic-tenant',company:'synthetic-company',phase:'PENDING',version:0,sample_reserved_minor:0,sample_observed_minor:0,sample_remaining_minor:1000,admission:'DENY',dispatch_allowed:false,spend_allowed:false,release_ready:false,actual_cost_minor:null,authoritative:false};
const state=(phase,version,reserved,observed,remaining)=>({...base,phase,version,sample_reserved_minor:reserved,sample_observed_minor:observed,sample_remaining_minor:remaining});
test('all fixed states',()=>{for(const x of [base,state('RESERVED',1,100,0,900),state('SETTLED_SAMPLE',2,0,60,940),state('UNKNOWN_HOLD',2,100,0,900)])assert.ok(parse(x));});
test('unknown cannot release reservation',()=>assert.equal(parse(state('UNKNOWN_HOLD',2,0,0,1000)),null));
test('authority flags and actual cost',()=>{for(const k of ['dispatch_allowed','spend_allowed','release_ready','authoritative'])assert.equal(parse({...base,[k]:true}),null);assert.equal(parse({...base,actual_cost_minor:0}),null);});
test('scope and unknown fields',()=>{assert.equal(parse({...base,company:'other'}),null);assert.equal(parse({...base,principal:'demo'}),null);});
test('version/amount consistency',()=>{assert.equal(parse({...base,version:1}),null);assert.equal(parse({...base,sample_remaining_minor:999}),null);assert.equal(parse({...base,phase:'toString'}),null);});
async function mocked(fn,check){const old=global.fetch;global.fetch=fn;try{await check(await GET());}finally{global.fetch=old;}}
test('fixed loopback proxy',async()=>mocked(async(url,opts)=>{assert.equal(url,'http://127.0.0.1:8000/demo/v1/admission/sample-projection');assert.equal(opts.method,'GET');assert.equal(opts.redirect,'error');return Response.json(base);},async r=>{assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),base);}));
test('invalid contract HOLD',async()=>mocked(async()=>Response.json({...base,spend_allowed:true}),async r=>assert.equal(r.status,503)));
test('oversized body HOLD',async()=>mocked(async()=>Response.json({x:'a'.repeat(5000)}),async r=>assert.equal(r.status,503)));
test('network failure HOLD',async()=>mocked(async()=>{throw Error('down');},async r=>assert.equal(r.status,503)));
