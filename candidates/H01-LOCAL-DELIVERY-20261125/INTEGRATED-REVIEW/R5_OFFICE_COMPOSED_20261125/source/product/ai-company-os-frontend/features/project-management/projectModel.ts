/** Read-only D0 presentation. The canonical guard owns validation and waves. */
import {readPlanProjection,type PlanTask} from '../core-review/planProjection';
export type ProjectRow={task:PlanTask;wave:number};
export type ProjectView=Extract<ReturnType<typeof readPlanProjection>,{ok:true}> & {rows:ProjectRow[];roles:string[];gates:ProjectRow[];holdCount:number};
const gateRoles=new Set(['qa','independent-verifier','human-authority']);
export function projectView(input?:Parameters<typeof readPlanProjection>[0]):ProjectView|{ok:false;reason:string}{
 try{
  const view=readPlanProjection(input);if(!view.ok)return view;
  const rows=view.groups.flatMap((group,i)=>group.map(task=>({task,wave:i+1})));
  return {...view,rows,roles:[...new Set(rows.map(r=>r.task.role))],gates:rows.filter(r=>gateRoles.has(r.task.role)),holdCount:rows.filter(r=>r.task.state==='HOLD').length};
 }catch{return {ok:false,reason:'PLAN_INPUT_INVALID'};}
}
const normalize=(s:string)=>s.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i');
export function filterRows(rows:readonly ProjectRow[],query:string,role:string):ProjectRow[]{
 const words=normalize(query).trim().split(/\s+/).filter(Boolean);
 return rows.filter(({task:t})=>(role===''||t.role===role)&&words.every(w=>normalize([t.id,t.label,t.role,t.state].join(' ')).includes(w)));
}
export function projectContext(view:ProjectView,id:string){
 const row=view.rows.find(r=>r.task.id===id);
 return {row,prerequisites:row?view.rows.filter(r=>row.task.depends_on.includes(r.task.id)):[],followers:row?view.rows.filter(r=>r.task.depends_on.includes(id)):[]};
}
