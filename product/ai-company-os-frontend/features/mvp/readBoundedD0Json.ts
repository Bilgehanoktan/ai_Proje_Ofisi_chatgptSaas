/** Bound every asynchronous stage of a local-only D0 JSON proxy to one deadline.
 *  Not a production auth, tenant or egress adapter. */
function beforeDeadline<T>(work: Promise<T>, signal: AbortSignal, onLateValue?: (value: T) => void): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const abort = () => reject(Error('deadline'));
    signal.addEventListener('abort', abort, {once: true});
    work.then(
      value => {
        signal.removeEventListener('abort', abort);
        if (signal.aborted) {onLateValue?.(value); reject(Error('deadline')); return;}
        resolve(value);
      },
      error => {signal.removeEventListener('abort', abort); reject(error);},
    );
    // Attach handlers even when the deadline has already expired.
    if (signal.aborted) abort();
  });
}

function cancelResponse(response: Response): void {
  if (response.body && !response.body.locked) void response.body.cancel().catch(() => {});
}

export async function readBoundedD0Json(
  endpoint: string,
  parse: (body: unknown) => unknown,
  maxBytes: number,
): Promise<unknown> {
  const signal = AbortSignal.timeout(2500);
  const response = await beforeDeadline(fetch(endpoint, {
    method:'GET',cache:'no-store',redirect:'error',signal,headers:{Accept:'application/json'},
  }), signal, cancelResponse);
  if (signal.aborted) {cancelResponse(response); throw Error('deadline');}
  if (!response.ok || response.redirected || !/^[\t ]*application\/json[\t ]*(?:;[\t ]*charset[\t ]*=[\t ]*(?:utf-8|"utf-8")[\t ]*)?(?![\s\S])/i.test(response.headers.get('content-type')??'') || !response.body) {
    cancelResponse(response);
    throw Error('response');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', {fatal:true});
  let size = 0, text = '';
  try {
    for (;;) {
      const {done, value} = await beforeDeadline(reader.read(), signal);
      if (done) break;
      size += value.byteLength;
      if (size > maxBytes) throw Error('size');
      text += decoder.decode(value, {stream:true});
    }
    text += decoder.decode();
  } finally {
    // Never let an unresponsive transport's cleanup block a 503 response.
    void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
  const body: unknown = JSON.parse(text);
  if (!parse(body) || signal.aborted) throw Error('contract_or_deadline');
  return body;
}
