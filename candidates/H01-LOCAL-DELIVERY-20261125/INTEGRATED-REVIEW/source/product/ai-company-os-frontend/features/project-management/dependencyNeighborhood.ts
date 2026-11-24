/** Derived only from the original pinned plan; not a scheduler or causal history. */
import {projectView,type ProjectView,type ProjectRow} from './projectModel';
export function dependencyNeighborhood(input:ProjectView,id:string){
 const checked=projectView(input.plan);
 if(!checked.ok)return null;
 const rows=checked.rows,selected=rows.find(r=>r.task.id===id);
 if(!selected)return null;
 const byId=new Map(rows.map(r=>[r.task.id,r]));
 const followers=new Map<string,string[]>();
 for(const r of rows)for(const p of r.task.depends_on){const list=followers.get(p)??[];list.push(r.task.id);followers.set(p,list);}
 function collect(initial:readonly string[],next:(key:string)=>readonly string[]):ProjectRow[]{
  const seen=new Set<string>(),pending=[...initial];
  while(pending.length){const key=pending.pop()!;if(seen.has(key)||key===id||!byId.has(key))continue;seen.add(key);pending.push(...next(key));}
  return rows.filter(r=>seen.has(r.task.id));
 }
 const directParents=rows.filter(r=>selected.task.depends_on.includes(r.task.id));
 const directChildren=rows.filter(r=>(followers.get(id)??[]).includes(r.task.id));
 return {selected,directParents,directChildren,ancestors:collect(selected.task.depends_on,key=>byId.get(key)?.task.depends_on??[]),descendants:collect(followers.get(id)??[],key=>followers.get(key)??[]),decision:'HOLD' as const};
}
