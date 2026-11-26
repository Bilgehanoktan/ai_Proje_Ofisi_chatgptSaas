/** Visual layout only. Call after the canonical or draft DAG guard; never schedules tasks. */
export type GraphTask={id:string;label:string;role:string};
export type GraphLink={from:string;to:string;kind:'reference'|'draft'};
export type GraphNode=GraphTask&{x:number;y:number;wave:number};
export const NODE_WIDTH=172,NODE_HEIGHT=64;
export function graphPresentation(tasks:readonly GraphTask[],waves:readonly (readonly string[])[],links:readonly GraphLink[]){
 if(!tasks.length||tasks.length>100||!waves.length||waves.length>100||links.length>10000)return null;
 const byId=new Map(tasks.map(t=>[t.id,t]));
 if(byId.size!==tasks.length)return null;
 const nodes:GraphNode[]=[],seen=new Set<string>();
 const maxRows=Math.max(...waves.map(w=>w.length));
 for(const [wave,ids] of waves.entries()){
  if(!ids.length)return null;
  for(const [row,id] of ids.entries()){
   const task=byId.get(id);if(!task||seen.has(id))return null;seen.add(id);
   nodes.push({...task,x:24+wave*224,y:56+(maxRows-ids.length)*44+row*88,wave:wave+1});
  }
 }
 if(seen.size!==tasks.length)return null;
 const placed=new Map(nodes.map(n=>[n.id,n])),edgeKeys=new Set<string>();
 const edges=[];
 for(const e of links){
  const a=placed.get(e.from),b=placed.get(e.to),key=JSON.stringify([e.from,e.to]);
  if(!a||!b||a.wave>=b.wave||edgeKeys.has(key)||!['reference','draft'].includes(e.kind))return null;
  edgeKeys.add(key);const x=a.x+NODE_WIDTH,y=a.y+NODE_HEIGHT/2,tx=b.x,ty=b.y+NODE_HEIGHT/2;
  const d=b.wave===a.wave+1?`M${x} ${y} C${x+26} ${y} ${tx-26} ${ty} ${tx} ${ty}`:`M${x} ${y} H${x+20} V40 H${tx-20} V${ty} H${tx}`;
  edges.push({...e,d});
 }
 return {nodes,edges,width:48+(waves.length-1)*224+NODE_WIDTH,height:56+(maxRows-1)*88+NODE_HEIGHT+24};
}
/** Role template association to a static plan only; no assignment to a real instance. */
export function rolePlanTasks(tasks:readonly GraphTask[],role:string){
 return tasks.filter(t=>t.role===role).map(t=>({id:t.id,label:t.label}));
}
