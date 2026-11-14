/** Quarantined D0 readback candidate; not mounted in R11. No authority or write routes. */
import {NextResponse} from 'next/server';
import snapshot from '../../../../fixtures/office.snapshot.json';
import plan from '../../../../fixtures/core.plan.projection.json';
import catalog from '../../../../fixtures/company.catalog.json';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const base = 'http://127.0.0.1:8000';
const MAX_BYTES = 512 * 1024;
const endpoints = {
  status: '/demo/v1/status',
  snapshot: '/demo/v1/office/worlds/demo-world/snapshot',
  plan: '/demo/v1/core/plan-projection',
  catalog: '/demo/v1/catalog',
} as const;
function canonical(v: unknown): string {
  if (v === null || typeof v !== 'object') return JSON.stringify(v) ?? 'undefined';
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
  const o = v as Record<string, unknown>;
  return '{' + Object.keys(o).sort().map(k => JSON.stringify(k)+':'+canonical(o[k])).join(',') + '}';
}
async function read(path: string): Promise<unknown> {
  const response = await fetch(base + path, {method:'GET', cache:'no-store', redirect:'error', signal:AbortSignal.timeout(3000), headers:{Accept:'application/json'}});
  if (!response.ok || !response.headers.get('content-type')?.includes('application/json') || !response.body) throw new Error('D0_READBACK_HTTP');
  const reader = response.body.getReader();
  let total = 0; const parts: Uint8Array[] = [];
  try {
    while (true) {
      const {done,value} = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_BYTES) { await reader.cancel(); throw new Error('D0_READBACK_LIMIT'); }
      parts.push(value);
    }
  } finally { reader.releaseLock(); }
  const data = new Uint8Array(total); let offset=0;
  for (const part of parts) {data.set(part,offset); offset+=part.byteLength;}
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));
}
export async function GET() {
  try {
    const [s, o, p, c] = await Promise.all(Object.values(endpoints).map(read));
    const expected = {mode:'D0_SAMPLE_NO_RUNTIME',security_acceptance:'HOLD',release_ready:false,real_test:'NOT_RUN'};
    if (canonical(s)!==canonical(expected)||canonical(o)!==canonical(snapshot)||canonical(p)!==canonical(plan)||canonical(c)!==canonical(catalog)) throw new Error('D0_FIXTURE_MISMATCH');
    return NextResponse.json({status:'D0_READBACK_MATCH_ONLY',snapshot:o,plan:p,catalog:c,dispatch_allowed:false,release_ready:false},{headers:{'Cache-Control':'no-store'}});
  } catch {
    return NextResponse.json({status:'HOLD',reason:'D0_READBACK_UNAVAILABLE_OR_MISMATCH',dispatch_allowed:false,release_ready:false},{status:503,headers:{'Cache-Control':'no-store'}});
  }
}
