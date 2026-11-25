"use client";
import type {PlanTask} from '../features/core-review/planProjection';
export default function WorkflowProjection({groups,selected,onSelect}:{groups:readonly (readonly PlanTask[])[];selected:string;onSelect:(id:string)=>void}){
 return <div className="dag-waves eds-waves" aria-label="Doğrulanmış sentetik plan dalgaları">{groups.map((group,i)=><section key={i} className="dag-wave"><h4>Dalga {i+1}</h4>{group.map(t=><button type="button" key={t.id} aria-pressed={selected===t.id} onClick={()=>onSelect(t.id)}><strong>{t.label}</strong><small>{t.role} · {t.state==='HOLD'?'HOLD':'UNKNOWN'}</small></button>)}</section>)}</div>;
}
