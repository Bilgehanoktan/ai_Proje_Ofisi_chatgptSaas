'use client';
/** D0 readback source candidate. Never presents fixture data as actual agent state. */
import {useState} from 'react';
type Readback = {tenant:string; world:string; sequence:number; tasks:number; planId:string};
type State = {kind:'IDLE'|'CHECKING'|'HOLD'} | {kind:'MATCH'; data:Readback};
function record(value:unknown): Record<string,unknown> | null {
  return typeof value==='object' && value!==null && !Array.isArray(value) ? value as Record<string,unknown> : null;
}
function parseReadback(value:unknown): Readback | null {
  const r=record(value);
  if(!r || r.status!=='D0_READBACK_MATCH_ONLY' || r.dispatch_allowed!==false || r.release_ready!==false) return null;
  const s=record(r.snapshot), p=record(r.plan);
  if(!s || !p || s.schema_version!=='office.snapshot.v0-D0' || s.tenant_id!=='synthetic-tenant' || s.world_id!=='demo-world' || s.environment_id!=='A0_SAMPLE_ONLY' || s.snapshot_seq!==0 || s.data_status!=='D0_SAMPLE_NO_RUNTIME' || typeof p.plan_id!=='string' || p.dispatch_allowed!==false || p.release_ready!==false || !Array.isArray(p.tasks)) return null;
  return {tenant:s.tenant_id,world:s.world_id,sequence:s.snapshot_seq,tasks:p.tasks.length,planId:p.plan_id};
}
export default function LocalReadbackPanel(){
  const [state,setState]=useState<State>({kind:'IDLE'});
  async function inspect(){
    setState({kind:'CHECKING'});
    try {
      const r=await fetch('/api/local-mvp/readback',{method:'GET',cache:'no-store',signal:AbortSignal.timeout(5000),redirect:'error'});
      if(!r.ok || !r.headers.get('content-type')?.includes('application/json')) throw new Error('HOLD');
      const data=parseReadback(await r.json());
      setState(data?{kind:'MATCH',data}:{kind:'HOLD'});
    } catch {setState({kind:'HOLD'});}
  }
  return <section className="panel" aria-label="Yerel D0 bağlantı kontrolü">
    <h2>Yerel API bağlantısı</h2>
    <p>Backend üzerinden geri okunan sentetik örnek; gerçek ajan durumu veya bağımsız kabul değildir.</p>
    <button disabled={state.kind==='CHECKING'} onClick={inspect}>Bağlantıyı kontrol et</button>
    <p role="status">{state.kind==='MATCH'?'D0 readback eşleşti · gerçek çalışma yok':state.kind==='HOLD'?'HOLD · API erişilemedi veya kaynak uyuşmadı':state.kind==='CHECKING'?'Kontrol ediliyor':'Henüz kontrol edilmedi'}</p>
    {state.kind==='MATCH'&&<dl><dt>Tenant / World</dt><dd>{state.data.tenant} / {state.data.world}</dd><dt>Snapshot</dt><dd>{state.data.sequence}</dd><dt>Plan / görev sayısı</dt><dd>{state.data.planId} / {state.data.tasks}</dd></dl>}
  </section>;
}
