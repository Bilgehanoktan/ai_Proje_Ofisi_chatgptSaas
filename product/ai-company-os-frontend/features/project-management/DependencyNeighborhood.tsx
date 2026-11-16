"use client";
import {useState} from 'react';
import {dependencyNeighborhood} from './dependencyNeighborhood';
import type {ProjectView,ProjectRow} from './projectModel';
import styles from './ProjectStudio.module.css';
export default function DependencyNeighborhood({view,selected,onSelect}:{view:ProjectView;selected:string;onSelect:(id:string)=>void}){
 const [transitive,setTransitive]=useState(false),graph=dependencyNeighborhood(view,selected);
 if(!graph)return <p role="status">Bağımlılık bağlamı yok · HOLD</p>;
 const parents=transitive?graph.ancestors:graph.directParents,children=transitive?graph.descendants:graph.directChildren;
 const column=(label:string,rows:ProjectRow[])=><div className={styles.graphColumn}><strong>{label} · {rows.length}</strong>{rows.length?rows.map(r=><button type="button" key={r.task.id} onClick={()=>onSelect(r.task.id)}>{r.task.label}<small>Dalga {r.wave} · HOLD</small></button>):<small>—</small>}</div>;
 return <section className={styles.neighborhood} aria-label="Seçili görev bağımlılık grafiği"><div className="bar"><h3>Bağımlılık bağlamı</h3><button type="button" aria-pressed={transitive} onClick={()=>setTransitive(v=>!v)}>{transitive?'Tüm bağlantılar':'Doğrudan bağlantılar'}</button></div><div className={styles.graphGrid}>{column('Ön koşullar',parents)}<div className={styles.graphSelected}><small>Seçili görev</small><strong>{graph.selected.task.label}</strong><small>Dalga {graph.selected.wave} · HOLD</small></div>{column('Sonraki görevler',children)}</div><small>Doğrulanmış plan topolojisi; yürütme, takvim veya teslimat kanıtı değildir.</small></section>;
}
