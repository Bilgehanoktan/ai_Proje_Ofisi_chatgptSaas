'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync(__dirname+'/sse_capture_init.js','utf8');

function deferred(){let resolve,reject;const promise=new Promise((res,rej)=>{resolve=res;reject=rej});return {promise,resolve,reject};}
function setup(){
  const calls=[];
  const win={location:{href:'http://127.0.0.1:17300/',origin:'http://127.0.0.1:17300'}};
  win.fetch=function(...args){const d=deferred();calls.push({args,d});return d.promise;};
  vm.runInNewContext(code,{window:win,URL,Map,Number,Error});
  return {win,calls};
}
function response(text,url='http://127.0.0.1:17300/api/demo/shared-snapshot'){
  return {url,clone(){return {text:async()=>text}}};
}
async function main(){
  let pass=0;const ok=(value,message)=>{assert.ok(value,message);pass++;console.log('PASS '+pass+': '+message);};
  const {win,calls}=setup();const origin='http://127.0.0.1:17300';const path=origin+'/api/demo/shared-snapshot';
  ok(win.__mi10Capture.issued()===0&&!win.__mi10Capture.ready(1),'initial state has no stale body');
  const a=win.fetch(path);
  ok(win.__mi10Capture.issued()===1&&!win.__mi10Capture.ready(1),'request A issued but body not ready');
  calls[0].d.resolve(response('snapshot-A'));await a;
  ok(win.__mi10Capture.ready(1),'first clone body stored under sequence one');
  assert.equal(await win.__mi10Capture.take(1),'snapshot-A');
  ok(!win.__mi10Capture.ready(1),'consumed body A removed');
  const b=win.fetch(path);
  ok(win.__mi10Capture.issued()===2&&!win.__mi10Capture.ready(2),'pending B cannot read already-consumed A');
  await assert.rejects(()=>win.__mi10Capture.take(1),/MI10_FRESH_SSE_BODY_NOT_READY/);
  ok(true,'already-consumed A cannot be read twice');
  calls[1].d.resolve(response('snapshot-B'));await b;
  assert.equal(await win.__mi10Capture.take(2),'snapshot-B');
  ok(!win.__mi10Capture.ready(2),'second clone consumed only as sequence two');
  const c=win.fetch(path);
  ok(win.__mi10Capture.issued()===3&&!win.__mi10Capture.ready(3),'pending C cannot reuse B');
  calls[2].d.resolve(response('snapshot-C'));await c;
  assert.equal(await win.__mi10Capture.take(3),'snapshot-C');
  ok(!win.__mi10Capture.ready(3),'third clone consumed only as sequence three');
  const unrelated=win.fetch(origin+'/api/other');
  ok(win.__mi10Capture.issued()===3,'unrelated API fetch not counted as snapshot');
  calls[3].d.resolve(response('other-body',origin+'/api/other'));await unrelated;
  const external=win.fetch('https://example.invalid/api/demo/shared-snapshot');
  ok(win.__mi10Capture.issued()===3,'external origin not counted');
  calls[4].d.resolve(response('external','https://example.invalid/api/demo/shared-snapshot'));await external;
  const e=win.fetch(path),f=win.fetch(path);
  ok(win.__mi10Capture.issued()===5&&!win.__mi10Capture.ready(4)&&!win.__mi10Capture.ready(5),'two concurrent requests receive distinct sequence IDs');
  calls[6].d.resolve(response('out-of-order-F'));await f;
  ok(win.__mi10Capture.ready(5)&&!win.__mi10Capture.ready(4),'later response arrival never impersonates earlier sequence');
  assert.equal(await win.__mi10Capture.take(5),'out-of-order-F');
  calls[5].d.resolve(response('out-of-order-E'));await e;
  assert.equal(await win.__mi10Capture.take(4),'out-of-order-E');
  ok(true,'out-of-order responses map to original issue sequence');
  const bad=win.fetch(path);
  calls[7].d.resolve(response('wrong','https://example.invalid/api/demo/shared-snapshot'));
  await assert.rejects(bad,/MI10_SSE_RESPONSE_URL_MISMATCH/);
  ok(!win.__mi10Capture.ready(6),'unexpected response URL fails closed');
  const failed=win.fetch(path);
  calls[8].d.reject(new Error('network rejected'));
  await assert.rejects(failed,/network rejected/);
  ok(!win.__mi10Capture.ready(7),'failed request cannot supply stale body');
  assert.equal(calls.length,9);
  ok(true,'no extra fetches beyond exact nine calls in harness');
  console.log('RESULT '+pass+'/'+pass+' PASS: fresh body binding; 0 network; 0 browser; 0 product code.');
}
main().catch(err=>{console.error(err);process.exitCode=1});
