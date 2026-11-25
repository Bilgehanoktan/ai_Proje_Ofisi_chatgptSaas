/** Bounded, incremental D0 joint planner. One visual actor moves per edge. */
import type {GridCell} from './premiumRouting';
export type TrafficStep={actor:number;to:GridCell};
export type TrafficResult={status:'SEARCHING'|'SOLVED'|'NO_ROUTE'|'LIMIT';steps:TrafficStep[];expanded:number};
type Node={cells:GridCell[];parent:number;step:TrafficStep|null;g:number;h:number};
const key=(c:GridCell)=>c.join(',');
const stateKey=(a:readonly GridCell[])=>a.map(key).join('|');
const equal=(a:GridCell,b:GridCell)=>a[0]===b[0]&&a[1]===b[1];
const adjacent=[[1,0],[0,1],[-1,0],[0,-1]] as const;
export function createTrafficSearch(start:readonly GridCell[],goal:readonly GridCell[],walkable:(c:GridCell)=>boolean,fixed:ReadonlySet<string>=new Set(),limit=20000){
 const allowed=(c:GridCell)=>Number.isSafeInteger(c[0])&&Number.isSafeInteger(c[1])&&walkable(c)&&!fixed.has(key(c));
 const valid=Number.isSafeInteger(limit)&&limit>=1&&limit<=20000&&start.length>=2&&start.length<=4&&start.length===goal.length&&[...start,...goal].every(allowed)&&new Set(start.map(key)).size===start.length&&new Set(goal.map(key)).size===goal.length;
 const targets=goal.map(c=>[...c] as GridCell);
 const heuristic=(a:readonly GridCell[])=>a.reduce((n,c,i)=>n+Math.abs(c[0]-targets[i][0])+Math.abs(c[1]-targets[i][1]),0);
 const cells=start.map(c=>[...c] as GridCell);
 const nodes:Node[]=valid?[{cells,parent:-1,step:null,g:0,h:heuristic(cells)}]:[];
 const seen=new Map<string,number>(valid?[[stateKey(cells),0]]:[]),heap:number[]=valid?[0]:[];
 let result:TrafficResult={status:valid?'SEARCHING':'NO_ROUTE',steps:[],expanded:0};
 const less=(a:number,b:number)=>{const x=nodes[a],y=nodes[b];return x.g+2*x.h<y.g+2*y.h||(x.g+2*x.h===y.g+2*y.h&&(x.h<y.h||(x.h===y.h&&a<b)));};
 function push(n:number){let i=heap.length;heap.push(n);while(i>0){const p=(i-1)>>1;if(!less(heap[i],heap[p]))break;[heap[i],heap[p]]=[heap[p],heap[i]];i=p;}}
 function pop(){const first=heap[0],last=heap.pop()!;if(heap.length){heap[0]=last;let i=0;for(;;){let j=i*2+1;if(j>=heap.length)break;if(j+1<heap.length&&less(heap[j+1],heap[j]))j++;if(!less(heap[j],heap[i]))break;[heap[j],heap[i]]=[heap[i],heap[j]];i=j;}}return first;}
 // A caller may mutate its readback; never expose planner-owned records or cell tuples.
 function snapshot():TrafficResult{return {status:result.status,expanded:result.expanded,steps:result.steps.map(({actor,to})=>({actor,to:[to[0],to[1]]}))};}
 function finish(status:TrafficResult['status'],steps:TrafficStep[]=[]){result={status,steps,expanded:result.expanded};return snapshot();}
 function advance(budget=96):TrafficResult{
  if(result.status!=='SEARCHING')return snapshot();
  if(!Number.isSafeInteger(budget)||budget<1||budget>256)throw Error('TRAFFIC_BUDGET_INVALID');
  for(let i=0;i<budget&&heap.length;i++){
   const idx=pop(),n=nodes[idx];if(seen.get(stateKey(n.cells))!==idx)continue;
   result={...result,expanded:result.expanded+1};
   if(n.h===0){const steps:TrafficStep[]=[];for(let j=idx;nodes[j].parent!==-1;j=nodes[j].parent)steps.push(nodes[j].step!);return finish('SOLVED',steps.reverse());}
   for(let actor=0;actor<n.cells.length;actor++)for(const [dx,dy] of adjacent){
    const from=n.cells[actor],to:GridCell=[from[0]+dx,from[1]+dy];if(!allowed(to)||n.cells.some((c,k)=>k!==actor&&equal(c,to)))continue;
    const next=n.cells.slice();next[actor]=to;const id=stateKey(next),prior=seen.get(id);if(prior!==undefined&&nodes[prior].g<=n.g+1)continue;
    if(nodes.length>=limit)return finish('LIMIT');
    const j=nodes.length;nodes.push({cells:next,parent:idx,step:{actor,to},g:n.g+1,h:heuristic(next)});seen.set(id,j);push(j);
   }
  }
  return heap.length?snapshot():finish('NO_ROUTE');
 }
 return {advance};
}
