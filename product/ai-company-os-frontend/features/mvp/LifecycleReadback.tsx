"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import {inspectHistoricalJoin} from './historicalJoin';
import plan from '../../fixtures/core.plan.projection.json';
export default function LifecycleReadback({context}:{context:'ceo'|'office'|'workflow'|'finance'|'security'}){
 const {state,data,read}=useProjectionRead('lifecycle');
 const join=data?inspectHistoricalJoin(plan,data):null;
 const labels={ceo:'CEO / LIFECYCLE',office:'OFFICE / LIFECYCLE',workflow:'WORKFLOW / LIFECYCLE',finance:'FINANCE / SETTLEMENT',security:'SECURITY / READBACK'} as const;
 return <section className="panel projection-summary" aria-label={labels[context]}><div className="bar"><div><div className="eyebrow">{labels[context]}</div><h2>0196-L tarihsel görev örneği</h2><small>Ayrı sabit plan · gerçek ajan veya güncel run değil</small></div><button type="button" onClick={read}>Lifecycle kaydını oku</button></div><p role="status" className="projection-read-status" data-phase={state.phase}>{readStatus(state,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Sabit tarihsel örnek eşleşti · HOLD',hold:'Kayıt yok veya uyuşmuyor · HOLD'})}</p>
 {data&&<><p className="sub">{data.run_id} · {data.task_id} · rev {data.plan_revision.slice(7,19)}… · v{data.head_version}</p><ol className="lifecycle-timeline">{data.timeline.map(e=><li key={e.version}><strong>v{e.version} · {e.state}</strong><small>{e.kind}</small></li>)}</ol><div className="projection-summary-grid"><article><small>Örnek lease</small><strong>Kapandı · v{data.lease_version}</strong></article><article><small>Heartbeat rev</small><strong>{data.heartbeat_revision}</strong></article><article><small>Örnek bırakılan rezervasyon</small><strong>{data.sample_released_minor} minor {data.currency}</strong></article><article><small>Örnek tanınan maliyet</small><strong>{data.sample_recognized_minor} minor</strong></article></div></>}
 {join&&<p className="join-readback"><strong>Plan / DAG bağlantısı: HOLD</strong><small>{join.reason} · yalnız kimlik karşılaştırması; canlı eşleme yok.</small></p>}
 <p className="sub">Geometri JOIN_HOLD · bağımsız kabul HOLD · gerçek görev, harcama, model, retrieval ve yayın DENY. Mevcut ofis/DAG planıyla birleştirilmez.</p></section>;
}
