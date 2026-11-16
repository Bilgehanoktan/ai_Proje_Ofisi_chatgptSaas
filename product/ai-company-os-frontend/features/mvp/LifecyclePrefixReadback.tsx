"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import HistoricalEvidence from '../evidence/HistoricalEvidencePanel';
import {inspectPlanBinding} from '../data/projectionScope';
import {inspectHistoricalJoin} from './historicalJoin';
import plan from '../../fixtures/core.plan.projection.json';
export default function LifecyclePrefixReadback({context}:{context:'ceo'|'office'|'workflow'|'finance'|'security'|'capability'}){
 const {state,data,read,reset}=useProjectionRead('lifecycle-prefix');
 const join=data?inspectHistoricalJoin(plan,data):null;
 const binding=data?inspectPlanBinding(data,plan):null;
 return <section className="panel projection-summary" aria-label={context+' / historical prefix'}><div className="bar"><div><div className="eyebrow">D0 / HISTORICAL PREFIX</div><h2>Görev ve lease gözlemi</h2><small>0196-L ayrı tarihsel DB · terminal örneğiyle aynı an değil</small></div><div className="chips"><button type="button" disabled={state.phase==='loading'} onClick={read}>Görev örneğini oku</button><button type="button" disabled={state.phase==='idle'} onClick={reset}>Görev örneğini temizle</button></div></div><p role="status" className="projection-read-status" data-phase={state.phase}>{readStatus(state,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Tarihsel prefix eşleşti · HOLD',hold:'Kayıt yok veya uyuşmuyor · HOLD'})}</p>
 {data&&<><p className="sub">{data.run_id} · görev {data.task_id} · {data.state} · v{data.head_version} · attempt {data.attempt}</p><ol className="lifecycle-timeline">{data.timeline.map(e=><li key={e.version}><strong>v{e.version} · {e.state}</strong><small>{e.kind}</small></li>)}</ol><details key={data.plan_revision+':'+data.run_id+':'+data.head_version}><summary>Olay ayrıntıları ve filtreler</summary><HistoricalEvidence key={data.plan_revision+':'+data.run_id+':'+data.head_version} endpoint="lifecycle-prefix" phase={state.phase} data={data}/></details><dl className="prefix-facts"><div><dt>Lease kaydı</dt><dd>v{data.lease_version} · fence {data.fence}</dd></div><div><dt>Heartbeat / expiry (örnek tick)</dt><dd>{data.heartbeat_tick} / {data.expires_tick}</dd></div><div><dt>Lease güncelliği</dt><dd>{data.lease_freshness}</dd></div><div><dt>Örnek açık rezervasyon</dt><dd>{data.sample_outstanding_minor} minor {data.currency}</dd></div><div><dt>Model / Memory ACL</dt><dd>{data.model_binding} / {data.memory_acl}</dd></div><div><dt>Plan / Office eşleşmesi</dt><dd>{data.geometry_join}</dd></div></dl></>}
 {join&&<p className="join-readback"><strong>Plan / DAG bağlantısı: HOLD</strong><small>{join.reason} · {binding?.reason??'HOLD'} · yalnız kimlik karşılaştırması; canlı eşleme yok.</small></p>}
 <p className="sub">Tarihsel lease kaydı, güncel yetki veya aktif ajan anlamına gelmez. Terminal paneli ayrı örnek dosyadır; durumlar birleştirilmez. Gerçek bütçe, model, retrieval, hareket ve dispatch kapalı.</p></section>;
}
