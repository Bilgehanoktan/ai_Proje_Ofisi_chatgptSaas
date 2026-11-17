/** A5 isolated D0 floor/portal simulation; no canonical placement, publication or runtime authority. */
export type Cell = readonly [number,number];
export type Lifecycle = 'PLANNED'|'DRAFT'|'VALIDATING'|'APPROVAL_PENDING'|'PUBLISHED'|'ACTIVE'|'DRAINING'|'ARCHIVED';
export type Floor = Readonly<{id:string;revision:string;lifecycle:Lifecycle;walkable:readonly Cell[];departments:readonly string[]}>;
export type Stop = Readonly<{floorId:string;cell:Cell}>;
export type Portal = Readonly<{id:string;stops:readonly Stop[];capacity:number}>;
export type Actor = Readonly<{visualActorId:string;roleTemplateId:string;floorId:string;cell:Cell;agentInstanceId:null}>;
export type Token = Readonly<{revision:string;step:number}>;
type Request = Readonly<{id:string;actorId:string;from:Stop;to:Stop}>;
type Phase = 'IDLE'|'POSITIONING'|'BOARDING'|'TRAVEL'|'EXIT';
const id = (v:unknown):v is string => typeof v==='string' && /^d0-[a-z0-9][a-z0-9-]{0,62}$/.test(v);
const validCell = (c:unknown):c is Cell => Array.isArray(c)&&c.length===2&&c.every(n=>Number.isSafeInteger(n)&&n>=0&&n<256);
const copyCell = (c:Cell):Cell => Object.freeze([c[0],c[1]] as const);
const key = (s:Stop) => s.floorId+':'+s.cell.join(',');
const copyStop = (s:Stop):Stop => Object.freeze({floorId:s.floorId,cell:copyCell(s.cell)});
function fail(reason:string):never {throw Error(reason);}
const stages:readonly Lifecycle[]=['PLANNED','DRAFT','VALIDATING','APPROVAL_PENDING','PUBLISHED','ACTIVE','DRAINING','ARCHIVED'];
/** Describes review order only, never publishes or activates a floor. */
export function nextFloorReview(stage:Lifecycle):Lifecycle|null {const i=stages.indexOf(stage);return i<0||i===stages.length-1?null:stages[i+1];}
export function createDynamicFloors(input:Readonly<{mode:'D0_SYNTHETIC_FIXTURE';revision:string;floors:readonly Floor[];portals:readonly Portal[];actors:readonly Actor[]}>) {
 if(input.mode!=='D0_SYNTHETIC_FIXTURE'||!id(input.revision)||input.floors.length<1||input.floors.length>32||input.actors.length>128||input.portals.length>32)fail('FIXTURE_SCOPE');
 const revision=input.revision;
 const floors=new Map<string,{floor:Floor;cells:Set<string>}>();
 for(const f of input.floors){
  if(!id(f.id)||!id(f.revision)||!stages.includes(f.lifecycle)||floors.has(f.id)||f.walkable.length>65536||f.departments.some(d=>!id(d))||new Set(f.departments).size!==f.departments.length||f.walkable.some(c=>!validCell(c)))fail('INVALID_FLOOR');
  const cells=new Set(f.walkable.map(c=>c.join(',')));if(cells.size!==f.walkable.length||!cells.size)fail('INVALID_FLOOR_CELLS');
  floors.set(f.id,{floor:Object.freeze({id:f.id,revision:f.revision,lifecycle:f.lifecycle,walkable:Object.freeze(f.walkable.map(copyCell)),departments:Object.freeze([...f.departments])}),cells});
 }
 const walkable=(s:Stop)=>validCell(s.cell)&&floors.get(s.floorId)?.cells.has(s.cell.join(','))===true;
 const active=(s:Stop)=>walkable(s)&&floors.get(s.floorId)?.floor.lifecycle==='ACTIVE';
 const actors=new Map<string,Actor>();const occupied=new Map<string,string>();
 for(const a of input.actors){const s={floorId:a.floorId,cell:a.cell};if(!id(a.visualActorId)||!a.visualActorId.startsWith('d0-visual-')||!['orchestrator','research','engineer','qa'].includes(a.roleTemplateId)||a.agentInstanceId!==null||actors.has(a.visualActorId)||!active(s)||occupied.has(key(s)))fail('INVALID_ACTOR');actors.set(a.visualActorId,Object.freeze({visualActorId:a.visualActorId,roleTemplateId:a.roleTemplateId,floorId:a.floorId,cell:copyCell(a.cell),agentInstanceId:null}));occupied.set(key(s),a.visualActorId);}
 type Lift={portal:Portal;stops:Map<string,Stop>;queue:Request[];current:Request|null;phase:Phase;cabinFloorId:string};
 const lifts=new Map<string,Lift>();const endpoints=new Set<string>();
 for(const p of input.portals){if(!id(p.id)||lifts.has(p.id)||!Number.isSafeInteger(p.capacity)||p.capacity<1||p.capacity>128||p.stops.length<2||p.stops.length>32)fail('INVALID_PORTAL');const stops=new Map<string,Stop>();for(const s of p.stops){if(!walkable(s)||stops.has(s.floorId)||endpoints.has(key(s)))fail('INVALID_PORTAL_STOP');stops.set(s.floorId,copyStop(s));endpoints.add(key(s));}lifts.set(p.id,{portal:Object.freeze({id:p.id,capacity:p.capacity,stops:Object.freeze([...stops.values()])}),stops,queue:[],current:null,phase:'IDLE',cabinFloorId:p.stops[0].floorId});}
 const reservations=new Map<string,string>();const pending=new Map<string,string>();const used=new Set<string>();let step=0;let currentToken:Token=Object.freeze({revision,step});
 const token=():Token=>currentToken;
 const check=(t:Token)=>{if(t!==currentToken||t.revision!==revision||t.step!==step)fail('STALE_TOKEN');};
 const getLift=(p:string)=>lifts.get(p)??fail('UNKNOWN_PORTAL');
 const getActor=(a:string)=>actors.get(a)??fail('UNKNOWN_ACTOR');
 const snapshot=()=>Object.freeze({mode:'D0_SYNTHETIC_FIXTURE' as const,authoritative:false as const,geometryJoin:'HOLD' as const,token:token(),floors:Object.freeze([...floors.values()].map(f=>f.floor)),actors:Object.freeze([...actors.values()].map(a=>Object.freeze({...a,inTransit:pending.has(a.visualActorId)&&[...lifts.values()].some(l=>l.current?.actorId===a.visualActorId&&['TRAVEL','EXIT'].includes(l.phase))}))),portals:Object.freeze([...lifts.values()].map(l=>Object.freeze({id:l.portal.id,phase:l.phase,cabinFloorId:l.cabinFloorId,waitReason:l.phase==='IDLE'&&l.queue[0]&&(occupied.has(key(l.queue[0].to))||reservations.has(key(l.queue[0].to)))?'LANDING_BLOCKED':null,capacity:l.portal.capacity,queue:Object.freeze([...l.queue]),current:l.current}))),reservations:Object.freeze([...reservations].map(([cell,requestId])=>Object.freeze({cell,requestId}))) });
 const done=()=>{step++;currentToken=Object.freeze({revision,step});return snapshot();};
 function move(t:Token,actorId:string,to:Cell){check(t);const a=getActor(actorId),s={floorId:a.floorId,cell:to};if(pending.has(actorId)||!active(s)||Math.abs(a.cell[0]-to[0])+Math.abs(a.cell[1]-to[1])!==1||occupied.has(key(s))||reservations.has(key(s)))fail('MOVE_BLOCKED');occupied.delete(key(a));occupied.set(key(s),actorId);actors.set(actorId,Object.freeze({...a,cell:copyCell(to)}));return done();}
 function request(t:Token,portalId:string,requestId:string,actorId:string,targetFloorId:string){check(t);const l=getLift(portalId),a=getActor(actorId),from=l.stops.get(a.floorId),to=l.stops.get(targetFloorId);if(!id(requestId)||used.size>=10000||used.has(requestId)||pending.has(actorId)||!from||!to||from.floorId===to.floorId||!active(from)||!active(to)||key(a)!==key(from)||reservations.has(key(from))||l.queue.length>=l.portal.capacity)fail('REQUEST_BLOCKED');const r=Object.freeze({id:requestId,actorId,from,to});l.queue.push(r);used.add(requestId);pending.set(actorId,requestId);reservations.set(key(from),requestId);return done();}
 function cancel(t:Token,portalId:string,requestId:string){check(t);const l=getLift(portalId),i=l.queue.findIndex(r=>r.id===requestId);let r:Request;if(i>=0){r=l.queue.splice(i,1)[0];}else{if(!['BOARDING','POSITIONING'].includes(l.phase)||l.current?.id!==requestId)fail('CANCEL_BLOCKED');r=l.current!;l.current=null;l.phase='IDLE';reservations.delete(key(r.to));}reservations.delete(key(r.from));pending.delete(r.actorId);return done();}
 /** One explicit simulation step; FIFO head waits for a free destination. No wall-clock or motion claim. */
 function advance(t:Token,portalId:string){check(t);const l=getLift(portalId);if(l.phase==='IDLE'){const r=l.queue[0];if(!r||occupied.has(key(r.to))||reservations.has(key(r.to)))return snapshot();l.queue.shift();l.current=r;l.phase=l.cabinFloorId===r.from.floorId?'BOARDING':'POSITIONING';reservations.set(key(r.to),r.id);return done();}
  const r=l.current??fail('PORTAL_INVARIANT');const a=getActor(r.actorId);if(reservations.get(key(r.from))!==r.id||reservations.get(key(r.to))!==r.id||pending.get(r.actorId)!==r.id||occupied.get(key(r.from))!==r.actorId||occupied.has(key(r.to)))fail('PORTAL_INVARIANT');
  if(l.phase==='POSITIONING'){l.cabinFloorId=r.from.floorId;l.phase='BOARDING';return done();}if(l.phase==='BOARDING'){l.phase='TRAVEL';return done();}if(l.phase==='TRAVEL'){l.cabinFloorId=r.to.floorId;l.phase='EXIT';return done();}
  occupied.delete(key(r.from));occupied.set(key(r.to),r.actorId);actors.set(r.actorId,Object.freeze({...a,floorId:r.to.floorId,cell:r.to.cell}));reservations.delete(key(r.from));reservations.delete(key(r.to));pending.delete(r.actorId);l.current=null;l.phase='IDLE';return done();
 }
 return Object.freeze({snapshot,move,request,cancel,advance});
}
