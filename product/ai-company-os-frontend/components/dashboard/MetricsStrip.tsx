"use client";
import fixture from '../../fixtures/office.snapshot.json';
const metricIcons = ['◈','▣','₺','◇'];
export default function MetricsStrip(){
  return <div className="metrics">{fixture.metrics.map((m,i)=><div className="metric" key={m.metric_id}><small>{metricIcons[i]} &nbsp; {m.label}</small><div className="value">{m.value??'—'}</div><small>Veri doğrulanmadı</small></div>)}</div>;
}
