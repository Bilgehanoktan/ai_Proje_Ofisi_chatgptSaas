/** Presentation-only cooperative escape; no runtime authority. */
export type GridCell=readonly [number,number];
export type EscapeStep={actor:0|1;to:GridCell};
const key=(c:GridCell)=>c.join(',');
const equal=(a:GridCell,b:GridCell)=>a[0]===b[0]&&a[1]===b[1];
const moves=[[1,0],[0,1],[-1,0],[0,-1]] as const;
/** Exact two-actor joint BFS. Each edge moves exactly one actor; no swaps. */
export function pairEscape(start:readonly [GridCell,GridCell],goal:readonly [GridCell,GridCell],walkable:(c:GridCell)=>boolean,fixed:ReadonlySet<string>,limit=14400):EscapeStep[]|null{
 const allowed=(c:GridCell)=>walkable(c)&&!fixed.has(key(c));
 if(!Number.isSafeInteger(limit)||limit<1||limit>14400||[...start,...goal].some(c=>!allowed(c))||equal(start[0],start[1])||equal(goal[0],goal[1]))return null;
 type State={cells:readonly [GridCell,GridCell];prev:number;step:EscapeStep|null};
 const q:State[]=[{cells:start,prev:-1,step:null}],seen=new Set([start.map(key).join('|')]);
 for(let i=0;i<q.length;i++){
  const {cells}=q[i];if(equal(cells[0],goal[0])&&equal(cells[1],goal[1])){const steps:EscapeStep[]=[];for(let n=i;q[n].prev!==-1;n=q[n].prev)steps.push(q[n].step!);return steps.reverse();}
  for(const actor of [0,1] as const)for(const [dx,dy] of moves){
   const to:GridCell=[cells[actor][0]+dx,cells[actor][1]+dy];if(!allowed(to)||equal(to,cells[actor===0?1:0]))continue;
   const next:readonly [GridCell,GridCell]=actor===0?[to,cells[1]]:[cells[0],to];const id=next.map(key).join('|');if(seen.has(id))continue;
   if(q.length>=limit)return null;seen.add(id);q.push({cells:next,prev:i,step:{actor,to}});
  }
 }
 return null;
}
/** A stable subpixel tie-breaker, after the world-space foot/front footprint anchor. */
export function depthAt(worldY:number,worldX:number,kind:'furniture'|'actor'|'label'){return worldY*1024+Math.max(0,Math.min(1100,worldX))/2048+(kind==='actor'?1:kind==='label'?2:0);}
export function cameraViewport(scrollX:number,scrollY:number,width:number,height:number,zoom:number){const w=width/zoom,h=height/zoom;return {x:scrollX+(width-w)/2,y:scrollY+(height-h)/2,w,h};}
