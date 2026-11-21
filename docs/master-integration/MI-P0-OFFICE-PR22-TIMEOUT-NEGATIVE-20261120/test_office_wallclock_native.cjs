'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {GET} = require(process.argv[2]);

async function probe(handler, cap = 3550) {
 const prev = global.fetch;
 let signaled=false;
 try {
  global.fetch = (_url,options) => {
   assert.ok(options.signal instanceof AbortSignal);
   signaled=true;
   return handler();
  };
  const start=performance.now();
  const outcome=await Promise.race([
   GET().then(r=>r.status,()=> 'REJECTED'),
   new Promise(resolve=>setTimeout(()=>resolve('PENDING'),cap))
  ]);
  const ms=performance.now()-start;
  assert.equal(signaled,true);
  assert.equal(outcome,503,'expired Office GET must return D0 HOLD 503');
  return ms;
 }finally {global.fetch=prev;}
}

test('Office PR22 R2 real 2500ms unresolved fetch bounds 503', async()=>{
 const elapsed=await probe(()=>new Promise(()=>{}));
 assert.ok(elapsed>=2300&&elapsed<3550,'elapsed '+elapsed);
 console.log('OFFICE_WALLCLOCK unresolved-fetch '+elapsed.toFixed(0)+'ms HTTP503');
});

test('Office PR22 R2 real 2500ms stalled response stream bounds 503', async()=>{
 const elapsed=await probe(()=>Promise.resolve(new Response(new ReadableStream({start(){}}),{headers:{'content-type':'application/json'}})));
 assert.ok(elapsed>=2300&&elapsed<3550,'elapsed '+elapsed);
 console.log('OFFICE_WALLCLOCK stalled-reader '+elapsed.toFixed(0)+'ms HTTP503');
});

test('Office PR22 R2 ignored cancel cleanup never blocks 503', async()=>{
 const elapsed=await probe(()=>Promise.resolve(new Response(new ReadableStream({
  start(c){c.enqueue(new Uint8Array(5000));},
  cancel(){return new Promise(()=>{});}
 }),{headers:{'content-type':'application/json'}})));
 assert.ok(elapsed>=2300&&elapsed<3550,'elapsed '+elapsed);
 console.log('OFFICE_WALLCLOCK stalled-cancel '+elapsed.toFixed(0)+'ms HTTP503');
});
