type Metric={metric_id:string;label:string;value:unknown};
export function formatMetric(value:unknown):string{return typeof value==='number'&&Number.isFinite(value)?String(value):'—';}
const icons:Record<string,string>={active_runs:'◈',pending_decisions:'▣',revenue:'₺',verified_outputs:'◇'};
export default function MetricCards({metrics}:{metrics:readonly Metric[]}){
 return <section className="metrics eds-metrics" aria-label="Sentetik metrikler">{metrics.map(m=><article className="metric eds-card" key={m.metric_id}><h3><span aria-hidden="true">{icons[m.metric_id]??'◇'} </span>{m.label}</h3><div className="value eds-value">{formatMetric(m.value)}</div><small>Veri doğrulanmadı · STATIC_ONLY</small></article>)}</section>;
}
