type Metric={metric_id:string;label:string;value:unknown};
/** Formatting a number is not proof that it is an authoritative KPI. */
export function formatMetric(value:unknown):string{return typeof value==='number'&&Number.isFinite(value)?String(value):'—';}
const icons:Record<string,string>={active_runs:'◈',pending_decisions:'▣',revenue:'₺',verified_outputs:'◇'};
export default function MetricCards({metrics}:{metrics:readonly Metric[]}){
 // These inputs come exclusively from office.snapshot.json (STATIC_ONLY).
 // The current product has no accepted live KPI source for these four fields.
 return <section className="metrics eds-metrics" aria-label="Doğrulanmamış CEO metrikleri">{metrics.map(m=><article className="metric eds-card" key={m.metric_id}><h3><span aria-hidden="true">{icons[m.metric_id]??'◇'} </span>{m.label}</h3><div className="value eds-value" aria-label={`${m.label}: doğrulanmış değer yok`}>—</div><small>Gerçek veri yok · STATIC_ONLY · HOLD</small></article>)}</section>;
}
