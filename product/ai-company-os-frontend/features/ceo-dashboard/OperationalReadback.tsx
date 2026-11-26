"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import styles from './OperationalReadback.module.css';
const labels:Record<string,string>={orchestrator:'Yönetim',research:'Araştırma',engineer:'Mühendislik',qa:'Kalite'};
export default function OperationalReadback(){
 const {state,read,reset}=useProjectionRead('task-budget');
 const data=state.phase==='historical'?state.data:null;
 const expectedOfficeEvents=data?data.office.roles.reduce((total,role)=>total+role.total,0):null;
 return <section className="panel projection-summary" aria-label="CEO operasyon örneği">
  <div className="bar"><div><div className="eyebrow">CEO / OPERATION READBACK</div><h2>Operasyon örneği</h2><small>Tek eşleştirilmiş tarihsel D0 yanıtı · canlı KPI değil</small></div><div className="chips"><button type="button" onClick={read} disabled={state.phase==='loading'}>Operasyon kaydını oku</button><button type="button" onClick={reset} disabled={state.phase==='idle'}>Kaydı temizle</button></div></div>
  <p role="status" className="projection-read-status" data-phase={state.phase}>{readStatus(state,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Tarihsel örnek · DENY',hold:'Kayıt doğrulanamadı · HOLD'})}</p>
  <div className="projection-summary-grid"><article><small>Örnek ofis olayları</small><strong>{data?data.office.sample_event_count+'/'+expectedOfficeEvents:'—'}</strong></article><article><small>Research örnek olayı</small><strong>{data?data.research_event_seq===null?'Gözlenmedi':'#'+data.research_event_seq:'—'}</strong></article><article><small>Sentetik bütçe durumu</small><strong>{data?.budget.phase??'—'}</strong></article><article><small>Gerçek aktif run</small><strong>—</strong></article></div>
  {data&&<div className={styles.details}>
   <section className={styles.card} aria-label="Tarihsel rol gözlemleri"><h3>Rol bazında olay gözlemi</h3><small>Gözlenen örnek olay / beklenen örnek olay; performans değil.</small><div className={styles.rows}>{data.office.roles.map(r=><div className={styles.row} key={r.station_id}><span>{labels[r.role]??r.role}</span><meter min={0} max={r.total} value={r.observed} aria-label={(labels[r.role]??r.role)+' örnek olayları'}/><strong>{r.observed}/{r.total}</strong></div>)}</div></section>
   <section className={styles.card} aria-label="Sentetik bütçe kırılımı"><h3>Örnek bütçe kırılımı</h3><small>Minor birim · gerçek maliyet değildir.</small><dl className={styles.budget}><div><dt>Rezervasyon</dt><dd>{data.budget.sample_reserved_minor}</dd></div><div><dt>Gözlenen örnek</dt><dd>{data.budget.sample_observed_minor}</dd></div><div><dt>Kalan örnek</dt><dd>{data.budget.sample_remaining_minor}</dd></div></dl><p className={styles.hold}>Harcama ve yayın DENY</p></section>
   <p className={styles.source}>Eşleştirilmiş kayıt: <code>{data.pair_id}</code> · Bütçe revizyonu: {data.budget.version} · Atomiklik doğrulanmadı</p>
  </div>}
  <section aria-label="Veri kökeni ve yetki sınırları" className={styles.provenance}><h3>Veri kaynağı ve güven sınırı</h3><ul><li><span>Okuma kaynağı</span><strong><code>/api/demo/task-budget</code></strong></li><li><span>Kanıt kapsamı</span><strong>{data?'Şema doğrulandı · yalnız tarihsel D0':'Canlı operasyon doğrulanmadı · HOLD'}</strong></li><li><span>Gerçek görev / çalışan</span><strong>— · HOLD</strong></li><li><span>Gerçek harcama / yürütme</span><strong>DENY</strong></li></ul></section>
  <p className="sub">Causality UNPROVEN · Lease / geometry HOLD · Gerçek maliyet ve dispatch DENY. Ayrı ekran okumaları otomatik birleştirilmez.</p>
 </section>;
}
