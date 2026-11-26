'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readBoundedD0Json}=require(require('node:path').resolve(process.argv[2]));
const endpoint='http://127.0.0.1:8000/demo/v1/mvp/diagnostics';
const parse=body=>body?.mode==='D0';
const bytes=new TextEncoder().encode('{"mode":"D0"}');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function response({status=200,mime='application/json',data,stalledCancel=false}={}){
 let cancels=0;
 const stream=new ReadableStream({start(c){if(data)c.enqueue(data);},cancel(){cancels++;if(stalledCancel)return new Promise(()=>{});}});
 return {value:new Response(stream,{status,headers:{'content-type':mime}}),get cancels(){return cancels}};
}
async function withFetch(fn,body,controller=new AbortController()){
 const f=global.fetch,t=AbortSignal.timeout;
 try{global.fetch=fn;AbortSignal.timeout=()=>controller.signal;await body(controller);}
 finally{global.fetch=f;AbortSignal.timeout=t;}
}
for(const [name,options] of [['bad MIME',{mime:'text/html'}],['non-OK response',{status:502}],['ambiguous MIME',{mime:'application/json; charset=UTF-8, text/html'}]])test(`${name}: rejected response body is canceled`,async()=>{
 const r=response(options);await withFetch(async()=>r.value,async()=>{
  await assert.rejects(readBoundedD0Json(endpoint,parse,4096),/response/);
  assert.equal(r.cancels,1);assert.equal(r.value.body.locked,false);
 });
});
test('late response after deadline: body is canceled',async()=>{
 let finish;const r=response();const p=new Promise(resolve=>finish=resolve);
 await withFetch(()=>p,async ac=>{
  const read=readBoundedD0Json(endpoint,parse,4096);ac.abort();await assert.rejects(read,/deadline/);finish(r.value);await tick();assert.equal(r.cancels,1);assert.equal(r.value.body.locked,false);
 });
});
test('already aborted response: body is canceled',async()=>{
 const r=response(),ac=new AbortController();ac.abort();await withFetch(async()=>r.value,async()=>{
  await assert.rejects(readBoundedD0Json(endpoint,parse,4096),/deadline/);await tick();assert.equal(r.cancels,1);
 },ac);
});
test('rejected header with never-settling cancel does not block HOLD',async()=>{
 const r=response({mime:'text/html',stalledCancel:true});await withFetch(async()=>r.value,async()=>{
  let timer;try{await assert.rejects(Promise.race([readBoundedD0Json(endpoint,parse,4096),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('watchdog')),300)})]),/response/);assert.equal(r.cancels,1);}finally{clearTimeout(timer)}
 });
});
test('valid UTF-8 JSON retains exact value and fixed fetch policy',async()=>{
 await withFetch(async(url,opts)=>{assert.equal(url,endpoint);assert.equal(opts.method,'GET');assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');return new Response(bytes,{headers:{'content-type':'Application/JSON; charset="UTF-8"'}});},async()=>assert.deepEqual(await readBoundedD0Json(endpoint,parse,4096),{mode:'D0'}));
});
test('oversized body still cancels and unlocks',async()=>{
 const r=response({data:new Uint8Array(4097)});await withFetch(async()=>r.value,async()=>{await assert.rejects(readBoundedD0Json(endpoint,parse,4096),/size/);assert.equal(r.cancels,1);assert.equal(r.value.body.locked,false)});
});
test('unsafe JSON contract remains rejected',async()=>{
 await withFetch(async()=>Response.json({mode:'LIVE'}),async()=>await assert.rejects(readBoundedD0Json(endpoint,parse,4096),/contract_or_deadline/));
});
test('already-aborted rejecting fetch has no unhandled rejection',async()=>{
 const ac=new AbortController();ac.abort();await withFetch(async()=>{throw Error('network');},async()=>{
  await assert.rejects(readBoundedD0Json(endpoint,parse,4096),/deadline/);await tick();
 },ac);
});
