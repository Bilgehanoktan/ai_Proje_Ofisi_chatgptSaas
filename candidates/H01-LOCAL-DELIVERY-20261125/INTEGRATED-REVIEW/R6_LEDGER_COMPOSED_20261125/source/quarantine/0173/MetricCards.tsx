type Metric={metric_id:string;label:string;value:unknown};
export default function MetricCards({metrics}:{metrics:readonly Metric[]}){
 return <section className="eds-metrics" aria-label="Sentetik metrikler">{metrics.map(m=><article className="eds-card" key={m.metric_id}><h3>{m.label}</h3><div className="eds-value">{typeof m.value==='number'&&Number.isFinite(m.value)||typeof m.value==='string'?String(m.value):'—'}</div><small>Veri doğrulanmadı · STATIC_ONLY</small></article>)}</section>;
}
