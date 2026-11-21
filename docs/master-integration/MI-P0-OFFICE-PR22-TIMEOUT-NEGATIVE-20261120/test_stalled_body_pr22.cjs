'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { GET } = require(process.argv[2]);

async function guardedRun(makeResponse) {
  const originalFetch = global.fetch;
  const originalTimeout = AbortSignal.timeout;
  const controller = new AbortController();
  let signalSeen = false;
  try {
    AbortSignal.timeout = () => controller.signal;
    global.fetch = async (_url, opts) => {
      signalSeen = opts.signal === controller.signal;
      controller.abort();
      return makeResponse();
    };
    const result = await Promise.race([
      GET().then(r => r.status, e => 'REJECTED:' + e.message),
      new Promise(resolve => setTimeout(() => resolve('PENDING_AFTER_ABORT'), 120)),
    ]);
    assert.equal(signalSeen, true, 'exact signal must be handed to transport');
    return result;
  } finally {
    global.fetch = originalFetch;
    AbortSignal.timeout = originalTimeout;
  }
}

test('aborted transport with a stalled response stream must return 503', async () => {
  const status = await guardedRun(() => new Response(new ReadableStream({ start() {} }), {
    headers: { 'content-type': 'application/json' },
  }));
  assert.equal(status, 503, 'the HTTP route must not hang after its deadline aborts');
});

test('aborted transport with cancel() that never resolves must return 503', async () => {
  const status = await guardedRun(() => new Response(new ReadableStream({
    start(controller) { controller.enqueue(new Uint8Array(5000)); },
    cancel() { return new Promise(() => {}); },
  }), {headers: {'content-type':'application/json'}}));
  assert.equal(status, 503, 'unbounded reader.cancel() must not stop the deadline');
});



test('aborted signal with unresolved fetch() must return 503', async () => {
  const originalFetch = global.fetch;
  const originalTimeout = AbortSignal.timeout;
  const controller = new AbortController();
  controller.abort();
  try {
    AbortSignal.timeout = () => controller.signal;
    global.fetch = async () => new Promise(() => {});
    const status = await Promise.race([
      GET().then(r => r.status),
      new Promise(resolve => setTimeout(() => resolve('PENDING_AFTER_ABORT'), 120)),
    ]);
    assert.equal(status, 503, 'an unresponsive transport must not keep GET() pending');
  } finally {
    global.fetch = originalFetch;
    AbortSignal.timeout = originalTimeout;
  }
});
