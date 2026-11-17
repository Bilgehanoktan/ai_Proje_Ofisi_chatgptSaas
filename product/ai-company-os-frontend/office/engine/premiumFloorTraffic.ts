/** A5R2: exact A1/A2 geometry + A3 pure planner; A5R1 remains the sole D0 position writer. */
import {createVisualIdentityRegistry,type VisualActorSeed,type SyntheticStation} from './premiumActorIdentity';
import {hybridWalkable,hybridPath,type Cell,type Scale,type Layout} from './premiumHybridLayout';
import {createTrafficSearch,type TrafficStep} from './premiumTraffic';
import {createDynamicFloors,type Lifecycle,type Portal,type Actor} from './premiumDynamicFloors';
export type FloorSeed=Readonly<{floorId:string;scale:Scale;lifecycle:Lifecycle;actors:readonly VisualActorSeed[];stations?:readonly SyntheticStation[]}>;
export type FloorGoal=Readonly<{visualActorId:string;floorId:string;cell:Cell}>;
export type FloorToken=Readonly<{revision:string;sequence:number}>;
const id=(v:unknown):v is string=>typeof v==='string'&&/^d0-[a-z0-9][a-z0-9-]{0,30}$/.test(v);
const key=(c:Cell)=>c.join(',');
const equal=(a:Cell,b:Cell)=>key(a)===key(b);
const cell=(c:Cell):Cell=>Object.freeze([c[0],c[1]] as const);
const valid=(c:unknown):c is Cell=>Array.isArray(c)&&c.length===2&&c.every(Number.isSafeInteger);
const fail=(reason:string):never=>{throw Error(reason);};
const adjacent=[[1,0],[0,1],[-1,0],[0,-1]] as const;
/** Only exterior walkable approach cells. Never opens the original disabled portal. */
export function portalLandingCandidates(layout:Layout):readonly Cell[]{
 const z=layout.zones.find(z=>z.id===layout.portal.zoneId);if(!z||z.kind!=='FLOOR_PORTAL'||layout.portal.enabled!==false)return [];
 const r=z.rect,out:Cell[]=[];
 for(let y=Math.max(0,r.y-1);y<=r.y+r.h;y++)for(let x=Math.max(0,r.x-1);x<=r.x+r.w;x++){
  const outside=(x===r.x-1||x===r.x+r.w)&&y>=r.y&&y<r.y+r.h||(y===r.y-1||y===r.y+r.h)&&x>=r.x&&x<r.x+r.w;
  if(outside&&hybridWalkable(layout,[x,y])&&hybridPath(layout,layout.entry,[x,y]))out.push(cell([x,y]));
 }
 return Object.freeze(out);
}
export function createFloorTraffic(input:Readonly<{mode:'D0_SYNTHETIC_WORLD';revision:string;floors:readonly FloorSeed[];portals:readonly Portal[]}>){
 if(input.mode!=='D0_SYNTHETIC_WORLD'||!id(input.revision)||input.floors.length<1||input.floors.length>32)fail('WORLD_SCOPE');
 const revision=input.revision;
 const seen=new Set<string>();const homes=new Map<string,{floorId:string;stationId:string;roomId:string;departmentId:string;assetProfileId:string;anchor:Cell}>();
 const geometry=input.floors.map(f=>{
  if(!id(f.floorId)||seen.has(f.floorId)||!Array.isArray(f.actors)||(f.lifecycle!=='ACTIVE'&&f.actors.length))fail('FLOOR_SCOPE');seen.add(f.floorId);
  const registry=createVisualIdentityRegistry(f.scale,f.actors,f.stations??[]),layout=registry.layout;
  const scope=(s:string)=>f.floorId+'/'+s;
  const stations=registry.stations.map(s=>Object.freeze({...s,floorId:f.floorId,stationId:scope(s.stationId),roomId:scope(s.roomId),departmentId:f.floorId+'-'+s.departmentId.slice(3)}));
  const actors:Actor[]=registry.actors.map(a=>{if(homes.has(a.visualActorId))fail('DUPLICATE_WORLD_ACTOR');const s=stations.find(s=>s.stationId===scope(a.stationId))!;homes.set(a.visualActorId,Object.freeze({floorId:f.floorId,stationId:s.stationId,roomId:s.roomId,departmentId:s.departmentId,assetProfileId:a.assetProfileId,anchor:a.anchor}));return {visualActorId:a.visualActorId,roleTemplateId:a.roleTemplateId,floorId:f.floorId,cell:a.anchor,agentInstanceId:null};});
  const walkable:Cell[]=[];for(let y=0;y<layout.height;y++)for(let x=0;x<layout.width;x++)if(hybridWalkable(layout,[x,y]))walkable.push(cell([x,y]));
  const landings=portalLandingCandidates(layout).filter(c=>!stations.some(s=>equal(s.anchor,c)));
  const departments=Object.freeze([...new Set(stations.filter(s=>s.kind!=='PASSIVE').map(s=>s.departmentId))]);
  return {layout,landings,actors,floor:Object.freeze({id:f.floorId,revision:'d0-a1-'+f.scale+'-r1',lifecycle:f.lifecycle,walkable:Object.freeze(walkable),departments}),view:Object.freeze({floorId:f.floorId,lifecycle:f.lifecycle,layoutRevision:registry.layoutRevision,layout,rooms:Object.freeze(layout.zones.map(z=>Object.freeze({...z,id:scope(z.id)}))),stations:Object.freeze(stations),departments,landings:Object.freeze(landings)})};
 });
 const byFloor=new Map(geometry.map(f=>[f.floor.id,f]));
 for(const p of input.portals)for(const s of p.stops){const g=byFloor.get(s.floorId);if(!g||!valid(s.cell)||!g.landings.some(c=>equal(c,s.cell)))fail('PORTAL_LANDING_SCOPE');}
 const core=createDynamicFloors({mode:'D0_SYNTHETIC_FIXTURE',revision,floors:geometry.map(f=>f.floor),actors:geometry.flatMap(f=>f.actors),portals:input.portals});
 const goals=new Map<string,FloorGoal>();let sequence=0,token:FloorToken=Object.freeze({revision,sequence}),status:'READY'|'MOVING'|'PLANNING'|'HOLD'='READY',reason:string|null=null,cursor=0,advances=0,latched=false;
 let joint:{ids:string[];search:ReturnType<typeof createTrafficSearch>;steps:TrafficStep[]|null}|null=null;let jointSearches=0,jointMoves=0,localMoves=0;
 const check=(t:FloorToken)=>{if(t!==token)fail('STALE_WORLD_TOKEN');};
 const pending=(s:ReturnType<typeof core.snapshot>)=>new Set(s.portals.flatMap(p=>[...p.queue,...(p.current?[p.current]:[])].map(r=>r.actorId)));
 const snapshot=()=>{const s=core.snapshot();return Object.freeze({mode:'D0_SYNTHETIC_WORLD' as const,authoritative:false as const,geometryJoin:'HOLD' as const,token,status,reason,positionsVersion:s.token.step,metrics:Object.freeze({jointSearches,jointMoves,localMoves}),floors:Object.freeze(geometry.map(g=>g.view)),actors:Object.freeze(s.actors.map(a=>{const home=homes.get(a.visualActorId)!;return Object.freeze({...a,home,atHome:!a.inTransit&&a.floorId===home.floorId&&equal(a.cell,home.anchor),goal:goals.get(a.visualActorId)??null});})),portals:s.portals,reservations:s.reservations});};
 const finish=()=>{token=Object.freeze({revision,sequence:++sequence});return snapshot();};
 const reset=()=>{joint=null;advances=0;latched=false;status=goals.size?'PLANNING':'READY';reason=null;};
 const clearReached=()=>{for(const a of core.snapshot().actors){const g=goals.get(a.visualActorId);if(g&&a.floorId===g.floorId&&equal(a.cell,g.cell))goals.delete(a.visualActorId);}};
 function setGoals(t:FloorToken,updates:readonly FloorGoal[]){check(t);const s=core.snapshot(),busy=pending(s),next=new Map(goals),ids=new Set<string>();for(const g of updates){const a=s.actors.find(a=>a.visualActorId===g.visualActorId),f=byFloor.get(g.floorId);if(!a||!f||ids.has(g.visualActorId)||busy.has(g.visualActorId)||a.floorId!==g.floorId||!valid(g.cell)||!hybridWalkable(f.layout,g.cell)||s.reservations.some(r=>r.cell===g.floorId+':'+key(g.cell)))fail('INVALID_WORLD_GOAL');ids.add(g.visualActorId);next.set(g.visualActorId,Object.freeze({...g,cell:cell(g.cell)}));}
  const destinations=[...next.values()].map(g=>g.floorId+':'+key(g.cell));if(new Set(destinations).size!==destinations.length)fail('DUPLICATE_WORLD_GOAL');goals.clear();for(const [k,v] of next)goals.set(k,v);clearReached();reset();return finish();}
 function cancelGoal(t:FloorToken,actorId:string){check(t);if(!goals.has(actorId))fail('UNKNOWN_WORLD_GOAL');goals.delete(actorId);reset();return finish();}
 function requestTransfer(t:FloorToken,portalId:string,requestId:string,actorId:string,targetFloorId:string){check(t);if(goals.has(actorId))fail('MOVEMENT_PENDING');core.request(core.snapshot().token,portalId,requestId,actorId,targetFloorId);reset();return finish();}
 function cancelTransfer(t:FloorToken,portalId:string,requestId:string){check(t);core.cancel(core.snapshot().token,portalId,requestId);reset();return finish();}
 function advancePortal(t:FloorToken,portalId:string){check(t);const old=core.snapshot().token;const s=core.advance(old,portalId);if(s.token!==old)reset();return finish();}
 function route(layout:Layout,from:Cell,to:Cell,fixed:Set<string>):Cell|null{
  if(fixed.has(key(to)))return null;const q=[from],first=new Map<string,Cell|null>([[key(from),null]]);
  for(let i=0;i<q.length;i++){const c=q[i];if(equal(c,to))return first.get(key(c))??null;for(const [dx,dy] of adjacent){const n:Cell=[c[0]+dx,c[1]+dy],k=key(n);if(first.has(k)||fixed.has(k)||!hybridWalkable(layout,n))continue;first.set(k,first.get(key(c))??n);q.push(n);}}return null;
 }
 function advanceTraffic(t:FloorToken){check(t);if(!joint)clearReached();if(!goals.size){status='READY';reason=null;return finish();}if(latched)return finish();if(++advances>2048){status='HOLD';reason='GENERATION_LIMIT';latched=true;return finish();}
  const s=core.snapshot(),busy=pending(s),moving=s.actors.filter(a=>goals.has(a.visualActorId)&&!busy.has(a.visualActorId));
  const fixedFor=(floorId:string,except:readonly string[])=>new Set([...s.actors.filter(a=>a.floorId===floorId&&!except.includes(a.visualActorId)).map(a=>key(a.cell)),...s.reservations.filter(r=>r.cell.startsWith(floorId+':')).map(r=>r.cell.slice(floorId.length+1))]);
  const apply=(a:string,to:Cell)=>{core.move(core.snapshot().token,a,to);if(!joint)clearReached();status=goals.size?'MOVING':'READY';reason=null;};
  if(joint){if(joint.steps===null){const r=joint.search.advance(96);if(r.status==='SEARCHING'){status='PLANNING';return finish();}if(r.status==='SOLVED')joint.steps=r.steps.slice();else {joint=null;status='HOLD';reason='JOINT_'+r.status;latched=true;return finish();}}const edge=joint.steps.shift();if(edge){apply(joint.ids[edge.actor],edge.to);jointMoves++;if(!joint.steps.length){joint=null;clearReached();status=goals.size?'MOVING':'READY';}return finish();}joint=null;}
  for(let i=0;i<moving.length;i++){const a=moving[(cursor+i)%moving.length],g=goals.get(a.visualActorId)!,layout=byFloor.get(a.floorId)!.layout;const n=route(layout,a.cell,g.cell,fixedFor(a.floorId,[a.visualActorId]));if(n){cursor=(cursor+i+1)%moving.length;apply(a.visualActorId,n);localMoves++;return finish();}}
  // Use the exact A3 bounded joint planner only for a small same-floor blocked group; never instantiate a second position writer.
  for(const g of geometry){const group=moving.filter(a=>a.floorId===g.floor.id);if(group.length<2||group.length>4)continue;const ids=group.map(a=>a.visualActorId);joint={ids,search:createTrafficSearch(group.map(a=>a.cell),group.map(a=>goals.get(a.visualActorId)!.cell),c=>hybridWalkable(g.layout,c),fixedFor(g.floor.id,ids)),steps:null};jointSearches++;status='PLANNING';reason=null;return finish();}
  status='HOLD';reason='NO_SAFE_ROUTE';latched=true;return finish();
 }
 return Object.freeze({snapshot,setGoals,cancelGoal,requestTransfer,cancelTransfer,advancePortal,advanceTraffic});
}
