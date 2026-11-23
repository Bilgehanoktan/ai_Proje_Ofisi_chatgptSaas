'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readBoundedD0Json } = require('../dist/readBoundedD0Json.js');
const endpoint = 'http://127.0.0.1:11111/unused-no-network';
const strictObject = x => !!x && typeof x === 'object' && x.ok === true;
function mockResponse({type='application/json', content='{"ok":true}', status=200, noHeader=false, noBody=false} = {}) {
  const headers = new Headers();
  if (!noHeader) headers.set('content-type', type);
  const body = noBody ? null : new TextEncoder().encode(content);
  return new Response(body, {status, headers});
}
async function run(options, {parse=strictObject, max=4096}={}) {
  const original = globalThis.fetch;
  let calls=0;
  globalThis.fetch = async (url, settings)=>{
    calls++;
    assert.equal(url,endpoint);
    assert.equal(settings.method,'GET');
    assert.equal(settings.cache,'no-store');
    assert.equal(settings.redirect,'error');
    assert.equal(settings.headers.Accept,'application/json');
    assert.equal(settings.signal.aborted,false);
    return mockResponse(options);
  };
  try { return await readBoundedD0Json(endpoint,parse,max); }
  finally { globalThis.fetch=original; assert.equal(calls,1); }
}

test('valid JSON media type accepted', async()=>{
  assert.deepEqual(await run({}),{ok:true});
});
test('case/charset media type accepted',async()=>{
  assert.deepEqual(await run({type:'Application/JSON; Charset=UTF-8'}),{ok:true});
});
test('invalid application/jsonp rejected',async()=>{
  await assert.rejects(run({type:'application/jsonp'}),/response/);
});
test('invalid application/json-malformed rejected',async()=>{
  await assert.rejects(run({type:'application/json-malformed'}),/response/);
});
test('text/plain rejected',async()=>{
  await assert.rejects(run({type:'text/plain'}),/response/);
});
test('missing content-type rejected',async()=>{
  await assert.rejects(run({noHeader:true}),/response/);
});
test('non-2xx rejected',async()=>{
  await assert.rejects(run({status:503}),/response/);
});
test('missing response body rejected',async()=>{
  await assert.rejects(run({noBody:true}),/response/);
});
test('invalid JSON rejected',async()=>{
  await assert.rejects(run({content:'{invalid'}),SyntaxError);
});
test('oversized bounded JSON rejected',async()=>{
  await assert.rejects(run({content:JSON.stringify({ok:true,pad:'x'.repeat(5000)})}),/size/);
});
test('parser schema rejection preserved',async()=>{
  await assert.rejects(run({content:'{"ok":false}'}),/contract_or_deadline/);
});
