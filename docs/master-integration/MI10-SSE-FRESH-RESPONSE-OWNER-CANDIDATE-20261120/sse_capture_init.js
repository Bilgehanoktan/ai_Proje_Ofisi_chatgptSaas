/* MI-10 CI-only reference: associate each existing fetch with its own SSE clone.
 * No extra HTTP request, route interception, product API stub, or permission change.
 */
(() => {
  const upstream = window.fetch;
  const origin = window.location.origin;
  const targetPath = '/api/demo/shared-snapshot';
  let issued = 0;
  const bodies = new Map();

  window.__mi10Capture = Object.freeze({
    issued: () => issued,
    ready: (seq) => Number.isSafeInteger(seq) && bodies.has(seq),
    take: async (seq) => {
      if (!Number.isSafeInteger(seq) || !bodies.has(seq)) {
        throw new Error('MI10_FRESH_SSE_BODY_NOT_READY');
      }
      const body = bodies.get(seq);
      bodies.delete(seq); // A sequence can only be consumed once.
      return await body;
    }
  });

  window.fetch = function (...args) {
    const input = args[0];
    let matched = false;
    try {
      const name = typeof input === 'string' ? input : input.url;
      const url = new URL(name, window.location.href);
      matched = url.origin === origin && url.pathname === targetPath;
    } catch (_) {
      // Preserve native fetch behavior for unrelated malformed inputs.
    }
    const seq = matched ? ++issued : null;
    const promise = upstream.apply(this, args);
    if (!matched) return promise;
    return promise.then(response => {
      const actual = new URL(response.url, window.location.href);
      if (actual.origin !== origin || actual.pathname !== targetPath) {
        throw new Error('MI10_SSE_RESPONSE_URL_MISMATCH');
      }
      bodies.set(seq, response.clone().text());
      return response;
    });
  };
})();
