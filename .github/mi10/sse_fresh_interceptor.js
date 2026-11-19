(() => {
  // MI-10 D0-only diagnostic: one settled cloned body per exact fetch sequence.
  // No route mock, no additional fetch, and no mutation of application responses.
  const upstream = window.fetch;
  const records = [];
  Object.defineProperty(window, "__mi10FetchRecords", {
    value: records, writable: false, configurable: false
  });
  window.fetch = function (...args) {
    const first = args[0];
    const raw = typeof first === "string" ? first : first && first.url;
    let target;
    try {
      target = new URL(raw, window.location.href);
    } catch (error) {
      return upstream.apply(this, args);
    }
    if (target.origin !== window.location.origin || target.pathname !== "/api/demo/shared-snapshot") {
      return upstream.apply(this, args);
    }
    const record = {
      sequence: records.length + 1,
      requestUrl: target.href,
      responseUrl: null,
      finished: false,
      body: null,
      error: null
    };
    records.push(record);
    return upstream.apply(this, args).then(
      response => {
        record.responseUrl = response.url;
        try {
          response.clone().text().then(
            body => {
              record.body = body;
              record.finished = true;
            },
            error => {
              record.error = String(error);
              record.finished = true;
            }
          );
        } catch (error) {
          record.error = String(error);
          record.finished = true;
        }
        return response;
      },
      error => {
        record.error = String(error);
        record.finished = true;
        throw error;
      }
    );
  };
})()
