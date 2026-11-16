"use client";
import {useId,useState} from 'react';
import {readPlanProjection} from '../core-review/planProjection';
import {reviewDraft,type DraftEdge} from './draftGraph';
import styles from './ParallelStudio.module.css';
export default function WorkflowDraft(){
 const [edges,setEdges]=useState<DraftEdge[]>([]),[from,setFrom]=useState(''),[to,setTo]=useState(''),[message,setMessage]=useState('');
 const sourceId=useId(),targetId=useId(),base=readPlanProjection();
 if(!base.ok)return <section className="panel" role="alert">Workflow taslağı · HOLD · {base.reason}</section>;
 const review=reviewDraft(base.plan.tasks,edges);
 function add(){if(!base.ok)return;const next=[...edges,{from,to}],r=reviewDraft(base.plan.tasks,next);if(!r.ok){setMessage(r.reason+' · Taslak değişmedi');return;}setEdges(next);setMessage('Yerel taslak güncellendi · HOLD');}
 return <section className={`panel ${styles.studio}`} aria-label="Yerel workflow taslak editörü"><div className="bar"><div><div className="eyebrow">WORKFLOW / DESIGN SANDBOX</div><h2>Bağımlılık tasarım stüdyosu</h2><small>Kanonik plan değişmez · kayıt ve yürütme yok</small></div><span className="pill">DRAFT · HOLD</span></div>
 <div className={styles.controls}><label htmlFor={sourceId}>Ön koşul<select id={sourceId} value={from} onChange={e=>setFrom(e.target.value)}><option value="">Seçin</option>{base.plan.tasks.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label><label htmlFor={targetId}>Bağımlı görev<select id={targetId} value={to} onChange={e=>setTo(e.target.value)}><option value="">Seçin</option>{base.plan.tasks.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label><button type="button" disabled={!from||!to} onClick={add}>Taslak bağlantı ekle</button><button type="button" onClick={()=>{setEdges([]);setFrom('');setTo('');setMessage('Taslak sıfırlandı');}}>Sıfırla</button></div>
 <p role="status" className="sub">{message||'Referans bağlantılar korunur. Yalnız ek taslak bağlantılar düzenlenebilir.'}</p>
 {review.ok?<div className={styles.waves} role="region" aria-label="Taslak bağımlılık dalgaları" tabIndex={0}>{review.waves.map((wave,i)=><article className={styles.wave} key={i}><strong>Taslak dalga {i+1}</strong>{wave.map(id=><div className={styles.node} key={id}>{base.plan.tasks.find(t=>t.id===id)?.label??id}<small>HOLD</small></div>)}</article>)}</div>:<p role="alert">Taslak HOLD · {review.reason}</p>}
 <h3>Ek taslak bağlantılar</h3>{edges.length?<ul className={styles.edges}>{edges.map((e,i)=><li key={JSON.stringify(e)}><span>{e.from} → {e.to}</span><button type="button" onClick={()=>{setEdges(edges.filter((_,j)=>j!==i));setMessage('Taslak bağlantı kaldırıldı');}}>Kaldır</button></li>)}</ul>:<p className="sub">Ek bağlantı yok.</p>}<p className="sub">Dalga hesabı yalnız tasarım geri bildirimi; Orchestrator planı, QA/IV kapısı, dispatch veya release yetkisi değildir.</p></section>;
}
