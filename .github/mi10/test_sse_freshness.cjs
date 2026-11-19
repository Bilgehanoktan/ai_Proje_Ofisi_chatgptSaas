"use strict";
// Exact MI-10 browser interception source, exercised without any network/browser.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const js = fs.readFileSync(path.join(__dirname, "sse_fresh_interceptor.js"), "utf8");
const url = "http://127.0.0.1:17300/api/demo/shared-snapshot";
const waiting = [];
const window = {
  location: { origin: "http://127.0.0.1:17300", href: "http://127.0.0.1:17300/" },
  fetch: (...args) => new Promise((resolve, reject) => waiting.push({ args, resolve, reject }))
};
vm.runInNewContext(js, { window, URL });
const records = window.__mi10FetchRecords;
let checks = 0;
function check(actual, expected, msg) {
  assert.deepEqual(actual, expected, msg);
  checks++;
}
function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((a, b) => { resolve = a; reject = b; });
  return { promise, resolve, reject };
}
async function deliverFetch(which, body) {
  const req = waiting[which];
  const completion = deferred();
  const response = { url, clone: () => ({ text: () => completion.promise }) };
  req.resolve(response);
  return { completion, response };
}
(async () => {
  const a = window.fetch(url);
  check(records.length, 1, "first request allocated");
  const first = await deliverFetch(0, "A");
  check(await a, first.response, "original first response preserved");
  check([records[0].finished, records[0].body], [false, null], "do not read pending first response");
  first.completion.resolve("A");
  await Promise.resolve();
  check([records[0].finished, records[0].body], [true, "A"], "first clone resolved");

  const b = window.fetch(url);
  check(records.length, 2, "second request has own sequence");
  check([records[1].finished, records[1].body], [false, null], "second cannot reuse settled A");
  const second = await deliverFetch(1, "B");
  check(await b, second.response, "second original response preserved");
  check(records[1].body, null, "second still pending despite prior A");
  second.completion.resolve("B");
  await Promise.resolve();
  check([records[1].finished, records[1].body], [true, "B"], "second clone is fresh B");
  check(records[0].body, "A", "first body remains A");

  const c = window.fetch(url);
  check([records.length, records[2].body], [3, null], "third has no stale B");
  const third = await deliverFetch(2, "C");
  check(await c, third.response, "third original response preserved");
  third.completion.resolve("C");
  await Promise.resolve();
  check([records[2].finished, records[2].body], [true, "C"], "third clone is fresh C");
  check(Array.from(records, x => x.sequence), [1, 2, 3], "monotonic request identity");
  check(records.every(x => x.responseUrl === url), true, "exact response URLs");

  const other = window.fetch("http://127.0.0.1:17300/health");
  check(records.length, 3, "unrelated fetch is not recorded");
  waiting[3].resolve({ url: "http://127.0.0.1:17300/health" });
  await other;
  check(records.length, 3, "no extra snapshot fetch");
  console.log("MI10_SSE_FRESHNESS_NEGATIVE_REPRO=BLOCKED; " + checks + "/" + checks + " PASS; independent bodies A/B/C");
})().catch(error => { console.error(error); process.exitCode = 1; });
