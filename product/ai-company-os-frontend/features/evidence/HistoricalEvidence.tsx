"use client";
import {useId,useState} from 'react';
import {diagnosticFindings,historicalEvents,historicalMetrics,outboxEvidence} from './historicalEvidence';
import styles from './EvidenceStudio.module.css';
export default function HistoricalEvidence({endpoint,phase,data}:{endpoint:string;phase:string;data:unknown}){
 const [query,setQuery]=useState('');const searchId=useId();
 const findings=diagnosticFindings(endpoint,phase,data),events=historicalEvents(endpoint,phase,data),metrics=historicalMetrics(endpoint,phase,data),outbox=outboxEvidence(endpoint,phase,data);
 const matches=events.filter(e=>(e.kind+' '+e.state).toLowerCase().includes(query.trim().toLowerCase()));
 if(!findings.length&&!events.length&&!metrics.length&&!outbox)return null;
 return <section className={styles.details} aria-label="Tek tarihsel kanıt kaydı"><small>ÖRNEK KAYIT · GÜNCEL YETKİ HOLD</small>{metrics.length>0&&<dl className={styles.metricGrid}>{metrics.map(m=><div key={m.label}><dt>{m.label}</dt><dd>{m.value}<small> {m.unit}</small></dd></div>)}</dl>}{findings.length>0&&<details><summary>Motor tanılamaları ({findings.length})</summary><dl>{findings.map(f=><div key={f.engine}><dt>{f.engine}</dt><dd>{f.reason}</dd></div>)}</dl></details>}{events.length>0&&<div className={styles.timeline}><label htmlFor={searchId}>Olay ara<input id={searchId} type="search" value={query} onChange={e=>setQuery(e.target.value)}/></label><small role="status">{matches.length}/{events.length} kayıt · zaman bilgisi yok</small><ol>{matches.map(e=><li key={e.version} value={e.version}><strong>{e.state}</strong><small>{e.kind}</small></li>)}</ol>{!matches.length&&<p>Olay eşleşmedi.</p>}</div>}{outbox&&<dl><dt>Tek Outbox gözlemi (olay akışı değil)</dt><dd>{outbox.phase} · Nesil {outbox.generation} · Okuma: {outbox.readback}</dd></dl>}<small>Kaynaklar birleştirilmez; canlı KPI, gerçek finans, güvenlik kabulü veya yerleşim çıkarılmaz.</small></section>;
}
