/** Presentation only: consume canonical waves, never schedule or grant execution. */
export type VisualTask = {id:string;label:string;role:string;state:string;depends_on:readonly string[]};
export type VisualNode = {task:VisualTask;wave:number;x:number;y:number};
export type VisualEdge = {from:string;to:string;path:string};
export const GRAPH = {column:240,row:112,width:204,height:78,margin:20,header:38} as const;
export type Layout = {ok:true;nodes:VisualNode[];edges:VisualEdge[];width:number;height:number;waveCount:number}|{ok:false;reason:string};
export function layoutWaves(groups:readonly (readonly VisualTask[])[]):Layout {
 const hold=(reason:string)=>({ok:false as const,reason});
 if(!groups.length||groups.length>100)return hold('WAVE_COUNT');
 const count=groups.reduce((n,g)=>n+g.length,0);
 if(count>100||groups.some(g=>!g.length))return hold('TASK_COUNT');
 const rows=Math.max(...groups.map(g=>g.length));
 const nodes:VisualNode[]=[], byId=new Map<string,VisualNode>();
 for(const [wave,group] of groups.entries())for(const [i,task] of group.entries()){
  if(!task.id||byId.has(task.id)||task.state!=='HOLD'||new Set(task.depends_on).size!==task.depends_on.length)return hold('TASK_INVALID');
  const node={task,wave,x:GRAPH.margin+wave*GRAPH.column,y:GRAPH.header+GRAPH.margin+(rows-group.length)*GRAPH.row/2+i*GRAPH.row};
  nodes.push(node);byId.set(task.id,node);
 }
 const edges:VisualEdge[]=[];
 for(const n of nodes)for(const id of n.task.depends_on){
  const from=byId.get(id);
  if(!from||from.wave>=n.wave)return hold('EDGE_INVALID');
  const x1=from.x+GRAPH.width,y1=from.y+GRAPH.height/2,x2=n.x,y2=n.y+GRAPH.height/2;
  const mid=(x1+x2)/2;
  edges.push({from:id,to:n.task.id,path:`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2-5} ${y2}`});
 }
 return {ok:true,nodes,edges,width:GRAPH.margin*2+(groups.length-1)*GRAPH.column+GRAPH.width,height:GRAPH.header+GRAPH.margin*2+(rows-1)*GRAPH.row+GRAPH.height,waveCount:groups.length};
}
export function selectedContext(layout:Extract<Layout,{ok:true}>,id:string){
 const node=layout.nodes.find(n=>n.task.id===id);
 if(!node)return {node:undefined,upstream:[] as VisualNode[],downstream:[] as VisualNode[]};
 const up=new Set(node.task.depends_on),down=new Set(layout.edges.filter(e=>e.from===id).map(e=>e.to));
 return {node,upstream:layout.nodes.filter(n=>up.has(n.task.id)),downstream:layout.nodes.filter(n=>down.has(n.task.id))};
}
