'use strict';
// QA-only offline reproduction of MI-10 CI SSE interceptor; no browser or HTTP.
const assert=require('node:assert/strict');
const pending=[];
const window={
 location:{href:'http://127.0.0.1:17300/',origin:'http://127.0.0.1:17300'},
 fetch:function(url){return new Promise(resolve=>pending.push({url,resolve}));}
};
// Exact reviewed interception logic from Git blob
// 84997c31334e4684b159b5dbd799e3abdd40d301, translated into a Node harness.
(() => {
  const upstream = window.fetch;
  window.__mi10LastStreamBody = null;
  window.fetch = function(...args) {
    return upstream.apply(this, args).then(response => {
      const url = new URL(response.url, window.location.href);
      if (url.origin === window.location.origin && url.pathname === '/api/demo/shared-snapshot') {
        window.__mi10LastStreamBody = response.clone().text();
      }
      return response;
    });
  };
})();
const path='http://127.0.0.1:17300/api/demo/shared-snapshot';
const response=body=>({url:path,clone(){return {text:async()=>body}}});
(async()=>{
 const one=window.fetch(path);
 assert.equal(pending.length,1);
 pending[0].resolve(response('snapshot-A'));
 await one;
 assert.equal(window.__mi10LastStreamBody!==null,true);
 assert.equal(await window.__mi10LastStreamBody,'snapshot-A');
 console.log('PASS 1/5 initial clone');
 const two=window.fetch(path);
 assert.equal(pending.length,2);
 assert.equal(window.__mi10LastStreamBody!==null,true);
 assert.equal(await window.__mi10LastStreamBody,'snapshot-A');
 assert.notEqual(await window.__mi10LastStreamBody,'snapshot-B');
 console.log('PASS 2/5 negative: second request can read old A while B pending');
 pending[1].resolve(response('snapshot-B'));
 await two;
 assert.equal(await window.__mi10LastStreamBody,'snapshot-B');
 console.log('PASS 3/5 eventual body update to B');
 const three=window.fetch(path);
 assert.equal(pending.length,3);
 assert.equal(window.__mi10LastStreamBody!==null,true);
 assert.equal(await window.__mi10LastStreamBody,'snapshot-B');
 console.log('PASS 4/5 negative: third request can read old B while C pending');
 pending[2].resolve(response('snapshot-C'));
 await three;
 assert.equal(await window.__mi10LastStreamBody,'snapshot-C');
 console.log('PASS 5/5 eventual body update to C');
 console.log('RESULT: 5/5 isolated assertions; two stale-body cases reproduced.');
})().catch(error=>{console.error(error);process.exitCode=1});
