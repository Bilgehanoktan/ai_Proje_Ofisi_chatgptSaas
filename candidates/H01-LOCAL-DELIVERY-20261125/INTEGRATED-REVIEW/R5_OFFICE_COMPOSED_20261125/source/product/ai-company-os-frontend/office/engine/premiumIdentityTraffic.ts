/** A3 D0 single-floor, integer-tick movement on the A2 identity registry. No runtime authority. */
import type {createVisualIdentityRegistry} from './premiumActorIdentity';
import {hybridWalkable,type Cell} from './premiumHybridLayout';
import {createTrafficSearch,type TrafficStep} from './premiumTraffic';
export type Registry=ReturnType<typeof createVisualIdentityRegistry>;
export type Goal=Readonly<{visualActorId:string;cell:Cell}>;
export type Movement=Readonly<{visualActorId:string;from:Cell;to:Cell;tick:number}>;
export type TrafficStatus='READY'|'MOVING'|'PLANNING'|'HOLD';
export type TrafficToken=Readonly<{layoutRevision:string;generation:number;tick:number}>;
const key=(c:Cell)=>c.join(',');
const equal=(a:Cell,b:Cell)=>a[0]===b[0]&&a[1]===b[1];
const cell=(c:Cell):Cell=>Object.freeze([c[0],c[1]] as const);
const validCell=(c:unknown):c is Cell=>Array.isArray(c)&&c.length===2&&c.every(Number.isSafeInteger);
const directions=[[1,0],[0,1],[-1,0],[0,-1]] as const;
const order=(a:string,b:string)=>a<b?-1:a>b?1:0;
type State={id:string;position:Cell;goal:Cell;waitTicks:number};
type Joint={ids:string[];search:ReturnType<typeof createTrafficSearch>;expanded:number};
export function createIdentityTraffic(registry:Registry){
 const layout=registry.layout, revision=registry.layoutRevision;
 if(registry.mode!=='D0_VISUAL_IDENTITY'||registry.geometryJoin!=='HOLD'||registry.authoritative!==false||registry.actors.some(a=>a.agentInstanceId!==null||a.floorId!=='D0-F1'||a.layoutRevision!==revision))throw Error('D0_REGISTRY_REQUIRED');
 const states:State[]=registry.actors.map(a=>({id:a.visualActorId,position:cell(a.anchor),goal:cell(a.anchor),waitTicks:0})).sort((a,b)=>order(a.id,b.id));
 const lookup=new Map(states.map(s=>[s.id,s]));
 if(lookup.size!==states.length||new Set(states.map(s=>key(s.position))).size!==states.length||states.some(s=>!hybridWalkable(layout,s.position)))throw Error('INVALID_INITIAL_OCCUPANCY');
 // Immutable per-floor adjacency; all dynamic barriers are separate local presentation data.
 const graph=new Map<string,Cell[]>();
 for(let y=0;y<layout.height;y++)for(let x=0;x<layout.width;x++)if(hybridWalkable(layout,[x,y]))graph.set(key([x,y]),directions.map(([dx,dy])=>cell([x+dx,y+dy])).filter(c=>hybridWalkable(layout,c)));
 let blocked=new Set<string>(),tick=0,generation=0,cursor=0,status:TrafficStatus='READY',reason:string|null=null;
 let movements:Movement[]=[],joint:Joint|null=null,escape:{ids:string[];steps:TrafficStep[]}|null=null;
 const failed=new Set<string>();let holdLatched=false,bfsExpanded=0,jointExpanded=0,moveCount=0;
 // Bound a command generation even if greedy routes keep moving without converging.
 const stateVisits=new Map<string,number>();let generationTicks=0;const MAX_GENERATION_TICKS=2048,MAX_STATE_VISITS=8;
 const allowed=(c:Cell)=>graph.has(key(c))&&!blocked.has(key(c));
 function path(from:Cell,to:Cell,occupied:ReadonlySet<string>):Cell[]|null{
  if(!allowed(from)||!allowed(to)||occupied.has(key(to)))return null;
  const q=[from],prev=new Map<string,Cell|null>([[key(from),null]]);
  for(let i=0;i<q.length;i++){const c=q[i];bfsExpanded++;if(equal(c,to)){const out:Cell[]=[];let p:Cell|null=c;while(p){out.unshift(p);p=prev.get(key(p))??null;}return out;}
   for(const n of graph.get(key(c))??[])if(!blocked.has(key(n))&&!occupied.has(key(n))&&!prev.has(key(n))){prev.set(key(n),c);q.push(n);}}
  return null;
 }
 const token=():TrafficToken=>Object.freeze({layoutRevision:revision,generation,tick});
 const check=(t:TrafficToken)=>{if(!t||t.layoutRevision!==revision||t.generation!==generation||t.tick!==tick)throw Error('STALE_TRAFFIC_TOKEN');};
 function invalidate(){stateVisits.clear();generationTicks=0;joint=null;escape=null;failed.clear();holdLatched=false;movements=[];status=states.every(s=>equal(s.position,s.goal))?'READY':'PLANNING';reason=null;}
 function setGoals(t:TrafficToken,goals:readonly Goal[]){
  check(t);const updates=new Map<string,Cell>();
  for(const g of goals){if(!g||!lookup.has(g.visualActorId)||updates.has(g.visualActorId)||!validCell(g.cell)||!allowed(g.cell))throw Error('INVALID_GOAL');updates.set(g.visualActorId,cell(g.cell));}
  const next=states.map(s=>updates.get(s.id)??s.goal);if(new Set(next.map(key)).size!==next.length)throw Error('DUPLICATE_GOAL');
  for(const s of states){const g=updates.get(s.id);if(g){s.goal=g;s.waitTicks=0;}}
  generation++;invalidate();return snapshot();
 }
 function setObstacles(t:TrafficToken,cells:readonly Cell[]){
  check(t);const next=new Set<string>();const occupied=new Set(states.map(s=>key(s.position)));
  for(const c of cells){if(!validCell(c)||!graph.has(key(c))||occupied.has(key(c))||next.has(key(c)))throw Error('INVALID_OBSTACLE');next.add(key(c));}
  blocked=next;generation++;invalidate();return snapshot();
 }
 function snapshot(){return Object.freeze({mode:'D0_IDENTITY_TRAFFIC' as const,geometryJoin:'HOLD' as const,authoritative:false as const,token:token(),floorId:'D0-F1',status,reason,actors:Object.freeze(states.map(s=>Object.freeze({visualActorId:s.id,cell:cell(s.position),goal:cell(s.goal),waitTicks:s.waitTicks}))),movements:Object.freeze(movements.map(m=>Object.freeze({...m,from:cell(m.from),to:cell(m.to)}))),obstacles:Object.freeze([...blocked].sort(order)),metrics:Object.freeze({bfsExpanded,jointExpanded,moveCount})});}
 // Reserve all start cells for this tick, plus every accepted target; never enter a vacated cell in the same tick.
 function apply(plans:readonly {s:State;to:Cell}[]){
  const reserved=new Set(states.map(s=>key(s.position)));const edges=new Set<string>();const ids=new Set<string>();
  for(const {s,to} of plans){const from=s.position,k=key(to),edge=key(from)+'>'+k,reverse=k+'>'+key(from);
   if(ids.has(s.id)||!allowed(to)||reserved.has(k)||edges.has(reverse)||Math.abs(from[0]-to[0])+Math.abs(from[1]-to[1])!==1)throw Error('TRAFFIC_INVARIANT');
   ids.add(s.id);reserved.add(k);edges.add(edge);}
  movements=plans.map(({s,to})=>({visualActorId:s.id,from:s.position,to:cell(to),tick}));
  for(const {s,to} of plans){s.position=cell(to);s.waitTicks=0;}
  moveCount+=plans.length;failed.clear();holdLatched=false;status='MOVING';reason=null;
 }
 function priority(){return states.map((_,i)=>states[(i+cursor)%states.length]).sort((a,b)=>b.waitTicks-a.waitTicks);}
 // Build conflict components from static shortest routes and current blockers, not a global 8–100 joint search.
 function groups():string[][]{
  const linked=new Map(states.map(s=>[s.id,new Set<string>()]));const positions=new Map(states.map(s=>[key(s.position),s.id]));
  for(const s of states){if(equal(s.position,s.goal))continue;const p=path(s.position,s.goal,new Set());if(!p)continue;
   for(const c of p.slice(1)){const other=positions.get(key(c));if(other&&other!==s.id){linked.get(s.id)!.add(other);linked.get(other)!.add(s.id);}}}
  const visited=new Set<string>(),out:string[][]=[];
  for(const s of priority()){if(visited.has(s.id)||!linked.get(s.id)!.size)continue;const group=[s.id];visited.add(s.id);for(let i=0;i<group.length;i++)for(const id of linked.get(group[i])!)if(!visited.has(id)){visited.add(id);group.push(id);}out.push(group.sort(order));}
  return out;
 }
 function advance(t:TrafficToken){
  check(t);tick++;movements=[];
  if(states.every(s=>equal(s.position,s.goal))){status='READY';reason=null;joint=null;escape=null;return snapshot();}
  for(const s of states)if(!equal(s.position,s.goal))s.waitTicks=Math.min(Number.MAX_SAFE_INTEGER,s.waitTicks+1);
  if(holdLatched){status='HOLD';return snapshot();}
  if(++generationTicks>MAX_GENERATION_TICKS){joint=null;escape=null;holdLatched=true;status='HOLD';reason='GENERATION_TICK_LIMIT';return snapshot();}
  if(states.length)cursor=(cursor+1)%states.length;
  if(escape){const step=escape.steps.shift();if(step){apply([{s:lookup.get(escape.ids[step.actor])!,to:step.to}]);if(!escape.steps.length)escape=null;return snapshot();}escape=null;}
  if(joint){const result=joint.search.advance(96);jointExpanded+=result.expanded-joint.expanded;joint.expanded=result.expanded;
   if(result.status==='SEARCHING'){status='PLANNING';reason=null;return snapshot();}
   if(result.status==='SOLVED'&&result.steps.length){escape={ids:joint.ids,steps:result.steps.slice()};joint=null;status='PLANNING';reason=null;return snapshot();}
   failed.add(joint.ids.join('|'));joint=null;
  }
  const reserved=new Set(states.map(s=>key(s.position)));const plans:{s:State;to:Cell}[]=[];
  for(const s of priority()){if(equal(s.position,s.goal))continue;const occupied=new Set(reserved);occupied.delete(key(s.position));const p=path(s.position,s.goal,occupied);if(p&&p.length>1){plans.push({s,to:p[1]});reserved.add(key(p[1]));}}
  if(plans.length){const stateKey=states.map(s=>key(s.position)).join('|');const visits=(stateVisits.get(stateKey)??0)+1;stateVisits.set(stateKey,visits);if(visits>MAX_STATE_VISITS){holdLatched=true;status='HOLD';reason='REPEATED_POSITION_LIMIT';return snapshot();}apply(plans);return snapshot();}
  const candidates=groups();
  for(const ids of candidates){if(ids.length<2||ids.length>4||failed.has(ids.join('|')))continue;
   const group=ids.map(id=>lookup.get(id)!);const fixed=new Set(states.filter(s=>!ids.includes(s.id)).map(s=>key(s.position)));
   joint={ids,search:createTrafficSearch(group.map(s=>s.position),group.map(s=>s.goal),allowed,fixed),expanded:0};status='PLANNING';reason=null;return snapshot();}
  status='HOLD';reason=candidates.some(g=>g.length>4)?'CONFLICT_GROUP_LIMIT':failed.size?'BOUNDED_RECOVERY_EXHAUSTED':'NO_SAFE_ROUTE';holdLatched=true;return snapshot();
 }
 return Object.freeze({snapshot,setGoals,setObstacles,advance});
}
