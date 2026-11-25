"use client";
import {useId,useState} from 'react';
import type {PlanTask} from '../features/core-review/planProjection';
import {GRAPH,layoutWaves,selectedContext} from './workflowLayout';
import styles from './WorkflowProjection.module.css';
import {studioContext} from '../features/mvp/studioContext';
export default function WorkflowProjection({groups,selected,onSelect}:{groups:readonly (readonly PlanTask[])[];selected:string;onSelect:(id:string)=>void}){
 const marker=useId().replace(/[^a-zA-Z0-9_-]/g,'');
 const [mode,setMode]=useState<'graph'|'list'>('graph');
 const layout=layoutWaves(groups);
 if(!layout.ok)return <div className="empty" role="alert">Görsel DAG HOLD · {layout.reason}</div>;
 const ctx=selectedContext(layout,selected);
 const agent=studioContext(ctx.node?.task);
 const related=new Set([...ctx.upstream,...ctx.downstream].map(n=>n.task.id));
 return <section className={styles.studio} aria-label="Sentetik Workflow Studio">
  <div className={styles.toolbar}><div><strong>Workflow Studio</strong><small>{layout.nodes.length} görev · {layout.edges.length} bağlantı · {layout.waveCount} dalga</small></div><div className="chips"><button type="button" aria-pressed={mode==='graph'} onClick={()=>setMode('graph')}>Grafik</button><button type="button" aria-pressed={mode==='list'} onClick={()=>setMode('list')}>Liste</button></div></div>
  <p className={styles.note}>D0 referans projeksiyonu · tüm görevler HOLD · yürütme veya düzenleme yok.</p>
  {mode==='graph'?<div className={styles.viewport} role="region" aria-label="Yatay kaydırılabilir görev grafı" tabIndex={0}><div className={styles.canvas} style={{width:layout.width,height:layout.height}}>
   <svg className={styles.edges} width={layout.width} height={layout.height} aria-hidden="true"><defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--muted)"/></marker></defs>{layout.edges.map(e=><path key={JSON.stringify([e.from,e.to])} d={e.path} className={e.from===selected||e.to===selected?styles.edgeActive:styles.edge} markerEnd={`url(#${marker})`}/>)}</svg>
   {Array.from({length:layout.waveCount},(_,i)=><div key={i} className={styles.wave} style={{left:GRAPH.margin+i*GRAPH.column,width:GRAPH.width}}>DALGA {String(i+1).padStart(2,'0')}</div>)}
   {layout.nodes.map(n=><button type="button" key={n.task.id} className={`${styles.node} ${related.has(n.task.id)?styles.related:''}`} style={{left:n.x,top:n.y,width:GRAPH.width,height:GRAPH.height}} aria-pressed={selected===n.task.id} onClick={()=>onSelect(n.task.id)}><strong>{n.task.label}</strong><small>{n.task.role} · HOLD</small></button>)}
  </div></div>:<div className={styles.list}>{groups.map((g,i)=><section key={i}><h4>Dalga {i+1}</h4>{g.map(t=><button type="button" key={t.id} aria-pressed={selected===t.id} onClick={()=>onSelect(t.id)}><strong>{t.label}</strong><small>{t.role} · HOLD · Bağlı: {t.depends_on.join(', ')||'—'}</small></button>)}</section>)}</div>}
  <div className={styles.context} aria-live="polite"><strong>{ctx.node?.task.label??'Görev seçilmedi'}</strong><div><small>Önceki görevler</small><span>{ctx.upstream.map(n=>n.task.label).join(' · ')||'—'}</span></div><div><small>Sonraki görevler</small><span>{ctx.downstream.map(n=>n.task.label).join(' · ')||'—'}</span></div><div><small>Plan rolü / Agent Studio</small><span>{agent?`${agent.roleLabel} · ${agent.agentLabel} · ${agent.decision}`: 'Görev seçilmedi · HOLD'}</span></div><small>Run ataması doğrulanmadı · Admission DENY · Release kapalı</small></div>
 </section>;
}
