'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {GET} = require(process.env.MI_P0_OFFICE_COMPILED_MODULE || './compiled/app/api/demo/office-workbench/route.js');

async function runWithControlledAbort(makeFetch) {
  const priorFetch = global.fetch;
  const priorTimeout = AbortSignal.timeout;
  const ctl = new AbortController();
  const observed = {fetch:false,read:false,cancel:false,passedSameSignal:false};
  try {
    AbortSignal.timeout = () => ctl.signal;
    global.fetch = async (url, opts) => {
      observed.fetch = true;
      observed.passedSameSignal = opts.signal === ctl.signal;
      assert.match(url, /^http:\/\/127\.0\.0\.1:8765\//);
      return makeFetch(ctl, observed);
    };
    const result = await Promise.race([
      GET().then(response => response.status, err => 'REJECTED:' + err.message),
      new Promise(resolve => setTimeout(() => resolve('TIMEOUT_NO_RESPONSE'), 250)),
    ]);
    return {result, observed};
  } finally {
    global.fetch = priorFetch;
    AbortSignal.timeout = priorTimeout;
  }
}

function responseWithReader(readerFactory) {
  const stream = new ReadableStream({start() {}});
  stream.getReader = () => readerFactory();
  return new Response(stream, {headers:{'content-type':'application/json'}});
}

test('after fetch resolved, reader.read that ignores abort returns HOLD 503', async () => {
  const {result,observed} = await runWithControlledAbort((ctl, seen) => {
    return responseWithReader(() => ({
      read() { seen.read=true; queueMicrotask(() => ctl.abort()); return new Promise(() => {}); },
      cancel() { return Promise.resolve(); },
      releaseLock() {},
    }));
  });
  assert.deepEqual({result,fetch:observed.fetch,read:observed.read,signal:observed.passedSameSignal},
    {result:503,fetch:true,read:true,signal:true});
});

test('after body read, reader.cancel that never resolves returns HOLD 503', async () => {
  const {result,observed} = await runWithControlledAbort((ctl, seen) => {
    return responseWithReader(() => ({
      read() { seen.read=true; return Promise.resolve({done:false,value:new Uint8Array(5000)}); },
      cancel() { seen.cancel=true; queueMicrotask(() => ctl.abort()); return new Promise(() => {}); },
      releaseLock() {},
    }));
  });
  assert.deepEqual({result,fetch:observed.fetch,read:observed.read,cancel:observed.cancel,signal:observed.passedSameSignal},
    {result:503,fetch:true,read:true,cancel:true,signal:true});
});

test('in-flight never resolving fetch after live signal returns HOLD 503', async () => {
  const {result,observed} = await runWithControlledAbort((ctl, seen) => {
    queueMicrotask(() => ctl.abort());
    return new Promise(() => {});
  });
  assert.deepEqual({result,fetch:observed.fetch,signal:observed.passedSameSignal},
    {result:503,fetch:true,signal:true});
});

test('valid JSON without abort still returns 200 with isolated stub parser', async () => {
  let count=0;
  const {result,observed} = await runWithControlledAbort((_ctl, seen) => {
    return responseWithReader(() => ({
      read() {seen.read=true;return Promise.resolve(count++ === 0 ?
        {done:false,value:new TextEncoder().encode('{"data":[]}')} : {done:true,value:undefined});},
      cancel() {return Promise.resolve();},releaseLock() {},
    }));
  });
  assert.deepEqual({result,fetch:observed.fetch,read:observed.read,signal:observed.passedSameSignal},
    {result:200,fetch:true,read:true,signal:true});
});
