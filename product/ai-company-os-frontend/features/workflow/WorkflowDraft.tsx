"use client";
import {useId,useRef,useState} from 'react';
import {readPlanProjection} from '../core-review/planProjection';
import {reviewDraft} from './draftGraph';
import {draftOverview} from './draftOverview';
import PlanGraph from '../graph/PlanGraph';
import {editDraft,emptyDraftHistory,type DraftAction} from './draftHistory';
import styles from './ParallelStudio.module.css';
export default function WorkflowDraft(){
 const [draft,setDraft]=useState(emptyDraftHistory),[from,setFrom]=useState(''),[to,setTo]=useState('');
 const [graphPick,setGraphPick]=useState<'from'|'to'>('from');
 const {edges,message}=draft;
 const dragSource=useRef<string|null>(null);
 const sourceId=useId(),targetId=useId(),base=readPlanProjection();
 if(!base.ok)return <section className="panel" role="alert">Workflow taslağı · HOLD · {base.reason}</section>;
 const review=reviewDraft(base.plan.tasks,edges);
 const summary=review.ok?draftOverview(review.waves,base.plan.edges.length,edges.length):null;
 function edit(action:DraftAction){if(base.ok)setDraft(current=>editDraft(base.plan.tasks,current,action));}
 function addEdge(source:string,target:string){edit({kind:'add',edge:{from:source,to:target}});}
 return <section className={`panel ${styles.studio}`} aria-label="Yerel workflow taslak editörü"><div className="bar"><div><div className="eyebrow">WORKFLOW / DESIGN SANDBOX</div><h2>Bağımlılık tasarım stüdyosu</h2><small>Kanonik plan değişmez · kayıt ve yürütme yok</small></div><span className="pill">DRAFT · HOLD</span></div>
 <div className={styles.controls}><label htmlFor={sourceId}>Ön koşul<select id={sourceId} value={from} onChange={e=>setFrom(e.target.value)}><option value="">Seçin</option>{base.plan.tasks.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label><label htmlFor={targetId}>Bağımlı görev<select id={targetId} value={to} onChange={e=>setTo(e.target.value)}><option value="">Seçin</option>{base.plan.tasks.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label><button type="button" disabled={!from||!to} onClick={()=>addEdge(from,to)}>Taslak bağlantı ekle</button><button type="button" disabled={!draft.past.length} onClick={()=>edit({kind:'undo'})}>Geri al</button><button type="button" disabled={!draft.future.length} onClick={()=>edit({kind:'redo'})}>İleri al</button><button type="button" onClick={()=>{dragSource.current=null;edit({kind:'reset'});setFrom('');setTo('');setGraphPick('from');}}>Sıfırla</button></div>
 <p role="status" className="sub">{message||'Bir görevi başka göreve sürükleyerek veya seçim kutularıyla bağlantı ekleyin. Referans bağlantılar korunur.'}</p>
 {summary&&<div className={styles.overview} aria-label="Taslak topoloji özeti"><span>Görev <strong>{summary.taskCount}</strong></span><span>Dalga <strong>{summary.waveCount}</strong></span><span>En geniş dalga <strong>{summary.largestWave}</strong></span><span>Referans bağlantı <strong>{summary.baseEdgeCount}</strong></span><span>Ek bağlantı <strong>{summary.addedEdgeCount}</strong></span></div>}
 {review.ok?<div className={styles.waves} role="region" aria-label="Taslak bağımlılık dalgaları" tabIndex={0}>{review.waves.map((wave,i)=><article className={styles.wave} key={i}><strong>Taslak dalga {i+1}</strong>{wave.map(id=><div className={styles.node} key={id} draggable onDragStart={e=>{dragSource.current=id;e.dataTransfer.effectAllowed="link";e.dataTransfer.setData("text/plain",id);}} onDragEnd={()=>{dragSource.current=null;}} onDragOver={e=>{if(dragSource.current){e.preventDefault();e.dataTransfer.dropEffect="link";}}} onDrop={e=>{e.preventDefault();const source=dragSource.current;dragSource.current=null;if(source)addEdge(source,id);}}>{base.plan.tasks.find(t=>t.id===id)?.label??id}<small>HOLD</small></div>)}</article>)}</div>:<p role="alert">Taslak HOLD · {review.reason}</p>}
 {review.ok&&<><div className="chips" role="group" aria-label="Grafikten bağlantı ucu seçimi"><button type="button" aria-pressed={graphPick==='from'} onClick={()=>setGraphPick('from')}>Ön koşulu seç</button><button type="button" aria-pressed={graphPick==='to'} onClick={()=>setGraphPick('to')}>Bağımlıyı seç</button></div><PlanGraph tasks={base.plan.tasks} waves={review.waves} links={[...base.plan.edges.map(e=>({...e,kind:'reference' as const})),...edges.map(e=>({...e,kind:'draft' as const}))]} selected={from} secondary={to} onSelect={id=>graphPick==='from'?setFrom(id):setTo(id)} label="Yerel taslak DAG"/><small>Grafik düğmeleri yalnız seçim kutularını doldurur. Bağlantı eklemek için yukarıdaki doğrulamalı ekleme işlemini kullanın.</small></>}
 <h3>Ek taslak bağlantılar · {edges.length}</h3>{edges.length?<ul className={styles.edges}>{edges.map(e=><li key={JSON.stringify(e)}><span>{e.from} → {e.to}</span><button type="button" onClick={()=>edit({kind:'remove',edge:e})}>Kaldır</button></li>)}</ul>:<p className="sub">Ek bağlantı yok.</p>}<p className="sub">Dalga hesabı yalnız tasarım geri bildirimi; Orchestrator planı, QA/IV kapısı, dispatch veya release yetkisi değildir.</p></section>;
}
