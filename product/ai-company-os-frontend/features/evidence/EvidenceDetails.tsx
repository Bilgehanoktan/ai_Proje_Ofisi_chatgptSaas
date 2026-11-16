"use client";
import {admissionBars,evidenceNotice} from './evidenceModel';
import styles from './EvidenceStudio.module.css';
import HistoricalEvidence from './HistoricalEvidence';
export default function EvidenceDetails({endpoint,phase,data}:{endpoint:string;phase:string;data:unknown}){
 const bars=admissionBars(endpoint,phase,data),max=Math.max(1,...bars.map(b=>b.value));
 return <div className={styles.details}><p role="status" className={styles.notice}>{evidenceNotice(phase)}</p>{phase==='historical'&&<details><summary>Kaynak ve kanıt sınırı</summary><dl><dt>Kaynak</dt><dd><code>/api/demo/{endpoint}</code></dd><dt>Güncellik</dt><dd>HISTORICAL_SAMPLE · canlı saat yok</dd><dt>Yetki</dt><dd>HOLD · bağımsız kabul yok</dd><dt>Bağlantı</dt><dd>Tek endpoint · çapraz kayıt birleştirilmez</dd></dl></details>}{bars.length>0&&<figure className={styles.chart}><figcaption>Tek örnek rezervasyon kaydı · minor birim</figcaption>{bars.map(b=><div className={styles.barRow} key={b.label}><span>{b.label}</span><meter min={0} max={max} value={b.value} aria-label={b.label}/><strong>{b.value}</strong></div>)}<small>Kalemler toplanmaz; gerçek maliyet veya bakiye değildir.</small></figure>}<HistoricalEvidence key={endpoint+':'+phase} endpoint={endpoint} phase={phase} data={data}/></div>;
}
