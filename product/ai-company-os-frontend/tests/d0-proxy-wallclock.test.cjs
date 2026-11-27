'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {resolve} = require('node:path');
const root = resolve(process.argv[2]);
const routes = ['admission','outbox','task-budget'];

async function measure(GET, handler, maxMs = 3550) {
  const old = global.fetch;
  let observedSignal = false;
  try {
    global.fetch = (url, options) => {
      assert.equal(url.startsWith('http://127.0.0.1:8000/demo/v1/'), true);
      assert.ok(options.signal instanceof AbortSignal);
      observedSignal = true;
      return handler();
    };
    const start = performance.now();
    const status = await Promise.race([
      GET().then(r => r.status, () => 'REJECTED'),
      new Promise(resolve => setTimeout(() => resolve('STILL_PENDING'), maxMs)),
    ]);
    const elapsed = performance.now() - start;
    assert.equal(observedSignal, true);
    assert.equal(status, 503, `expired D0 GET must return 503, got ${status}`);
    return elapsed;
  } finally {
    global.fetch = old;
  }
}

for (const name of routes) {
  const {GET} = require(resolve(root, `app/api/demo/${name}/route.js`));
  test(`${name}: actual AbortSignal.timeout(2500) bounds ignored fetch`, async () => {
    const elapsed = await measure(GET, () => new Promise(() => {}));
    assert.ok(elapsed >= 2300 && elapsed < 3550, `deadline elapsed ${elapsed.toFixed(0)}ms`);
    console.log(`WALLCLOCK ${name} unresolved-fetch ${elapsed.toFixed(0)}ms status=503`);
  });
}
const {GET: admission} = require(resolve(root,'app/api/demo/admission/route.js'));
test('admission: actual 2500ms timer bounds unread stalled stream', async () => {
  const elapsed = await measure(admission, () => Promise.resolve(new Response(
    new ReadableStream({start() {}}), {headers:{'content-type':'application/json'}}
  )));
  assert.ok(elapsed >= 2300 && elapsed < 3550, `deadline elapsed ${elapsed.toFixed(0)}ms`);
  console.log(`WALLCLOCK admission stalled-reader ${elapsed.toFixed(0)}ms status=503`);
});
test('admission: cancel cleanup never settling cannot hang 503', async () => {
  const elapsed = await measure(admission, () => Promise.resolve(new Response(
    new ReadableStream({start(c) {c.enqueue(new Uint8Array(12000));},cancel() {return new Promise(() => {});}}),
    {headers:{'content-type':'application/json'}}
  )), 3550);
  assert.ok(elapsed < 1000, `cleanup should fail fast, got ${elapsed.toFixed(0)}ms`);
  console.log(`WALLCLOCK admission stalled-cancel ${elapsed.toFixed(0)}ms status=503`);
});
