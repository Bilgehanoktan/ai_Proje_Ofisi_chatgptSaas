const lanes=['A','B','C','D','E','F','G','H'] as const;
const kinds=['SOURCE','HELPER_TEST','PARENT_TEST','INTEGRATED_TEST','ACCEPTANCE'] as const;
type Kind=typeof kinds[number];
type Gate={id:string;title:string;kind:Kind;status:'DONE'|'OPEN';evidence:string};
type Lane={id:typeof lanes[number];name:string;gates:Gate[]};
export type PlanProgress={id:'W1-0198-A-H';revision:string;lanes:Lane[]};
const record=(x:unknown):x is Record<string,unknown>=>!!x&&typeof x==='object'&&!Array.isArray(x);
/** Counts frozen milestone closures, not elapsed effort, product acceptance or ETA. */
export function parsePlanProgress(raw:unknown):PlanProgress|null{
 if(!record(raw)||raw.id!=='W1-0198-A-H'||typeof raw.revision!=='string'||!/^W1-0198-P\d{2}$/.test(raw.revision)||!Array.isArray(raw.lanes)||raw.lanes.length!==8)return null;
 const result:Lane[]=[];
 for(let i=0;i<lanes.length;i++){
  const l=raw.lanes[i];if(!record(l)||l.id!==lanes[i]||typeof l.name!=='string'||!l.name.trim()||!Array.isArray(l.gates)||l.gates.length!==5)return null;
  const gates:Gate[]=[];
  for(let j=0;j<5;j++){
   const g=l.gates[j];if(!record(g)||g.id!==`${lanes[i]}${j+1}`||typeof g.title!=='string'||!g.title.trim()||typeof g.evidence!=='string'||!g.evidence.trim()||!kinds.includes(g.kind as Kind)||(g.status!=='DONE'&&g.status!=='OPEN'))return null;
   gates.push({id:g.id,title:g.title,kind:g.kind as Kind,status:g.status,evidence:g.evidence});
  }
  result.push({id:lanes[i],name:l.name,gates});
 }
 return {id:raw.id,revision:raw.revision,lanes:result};
}
export function summarizePlan(raw:unknown){
 const p=parsePlanProgress(raw);if(!p)return null;
 const rows=p.lanes.map(l=>{const done=l.gates.filter(g=>g.status==='DONE').length;return {...l,done,total:l.gates.length,percent:done*100/l.gates.length};});
 const done=rows.reduce((n,l)=>n+l.done,0),total=rows.reduce((n,l)=>n+l.total,0);
 const accepted=rows.flatMap(l=>l.gates).filter(g=>g.kind==='ACCEPTANCE'&&g.status==='DONE').length;
 return {revision:p.revision,rows,done,total,percent:done*100/total,accepted};
}
