"use client";
import {useId} from 'react';
import {graphPresentation,NODE_WIDTH,NODE_HEIGHT,type GraphTask,type GraphLink} from './graphPresentation';
import styles from './PlanGraph.module.css';
export default function PlanGraph({tasks,waves,links,selected,secondary,onSelect,label}:{tasks:readonly GraphTask[];waves:readonly (readonly string[])[];links:readonly GraphLink[];selected?:string;secondary?:string;onSelect:(id:string)=>void;label:string}){
 const marker=useId().replace(/[^a-zA-Z0-9_-]/g,''),graph=graphPresentation(tasks,waves,links);
 if(!graph)return <p role="status">Grafik bağlamı doğrulanamadı · HOLD</p>;
 const labels=new Map(tasks.map(t=>[t.id,t.label]));
 return <section className={styles.graph} aria-label={label}>
  <div className={styles.legend}><span>━ Referans bağlantı</span><span>┄ Yerel taslak bağlantı</span><small>Dalga sırası zaman veya kapasite değildir · HOLD</small></div>
  <div className={styles.scroll} role="region" aria-label={label+' · yatay kaydırma'} tabIndex={0}>
   <div className={styles.canvas} style={{width:graph.width,height:graph.height}}>
    <svg className={styles.lines} width={graph.width} height={graph.height} aria-hidden="true" focusable="false"><defs><marker id={marker} markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6Z" fill="var(--muted)"/></marker></defs>{graph.edges.map(e=><path key={JSON.stringify([e.from,e.to])} d={e.d} className={styles.link} data-kind={e.kind} data-related={e.from===selected||e.to===selected||e.from===secondary||e.to===secondary} markerEnd={'url(#'+marker+')'}/>)}</svg>
    {waves.map((_,i)=><span key={i} className={styles.waveLabel} style={{left:24+i*224}}>Dalga {i+1}</span>)}
    {graph.nodes.map(n=><button key={n.id} type="button" className={styles.node} aria-pressed={selected===n.id||secondary===n.id} data-source={selected===n.id} data-target={secondary===n.id} style={{left:n.x,top:n.y,width:NODE_WIDTH,height:NODE_HEIGHT}} onClick={()=>onSelect(n.id)} title={n.label+' · '+n.role}><strong>{n.label}</strong><small>{n.role} · HOLD</small></button>)}
   </div>
  </div>
  <details className={styles.edges}><summary>Bağlantı listesi ({graph.edges.length})</summary><ul>{graph.edges.map(e=><li key={JSON.stringify([e.from,e.to])}>{labels.get(e.from)} → {labels.get(e.to)} · {e.kind==='draft'?'Taslak':'Referans'}</li>)}</ul></details>
 </section>;
}
