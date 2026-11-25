/** A2 D0 visual identity registry. Not runtime identity, placement, or movement authority. */
import {createHybridLayout,hybridPath,hybridWalkable,type Cell,type Role,type Scale} from './premiumHybridLayout';
export type VisualActorSeed=Readonly<{visualActorId:string;roleTemplateId:Role;stationId:string}>;
export type SyntheticStation=Readonly<{stationId:string;roleTemplateId:Role;anchor:Cell}>;
export type VisualStation=Readonly<{stationId:string;floorId:string;roomId:string;departmentId:string;roleTemplateId:Role|null;anchor:Cell;kind:'CORE'|'PASSIVE'|'SYNTHETIC_TEST';agentInstanceId:null}>;
export type VisualActor=Readonly<VisualActorSeed&{floorId:string;roomId:string;departmentId:string;assetProfileId:string;layoutRevision:string;anchor:Cell;agentInstanceId:null}>;
const roles=['orchestrator','research','engineer','qa'] as const;
const rooms:Readonly<Record<Role,string>>=Object.freeze({orchestrator:'F1-ORCH',research:'F1-RSCH',engineer:'F1-ENG',qa:'F1-QA'});
const roleOk=(v:unknown):v is Role=>roles.some(r=>r===v);
const idOk=(v:unknown):v is string=>typeof v==='string'&&/^d0-[a-z0-9][a-z0-9-]{0,62}$/.test(v);
const exact=(v:unknown,keys:readonly string[]):boolean=>!!v&&typeof v==='object'&&Object.keys(v).length===keys.length&&keys.every(k=>Object.prototype.hasOwnProperty.call(v,k));
const frozenCell=(c:Cell):Cell=>Object.freeze([c[0],c[1]] as const);
const seedRoles:readonly VisualActorSeed[]=Object.freeze([
 Object.freeze({visualActorId:'d0-visual-o',roleTemplateId:'orchestrator',stationId:'d0-o'}),
 Object.freeze({visualActorId:'d0-visual-r',roleTemplateId:'research',stationId:'d0-r'}),
 Object.freeze({visualActorId:'d0-visual-e',roleTemplateId:'engineer',stationId:'d0-e'}),
 Object.freeze({visualActorId:'d0-visual-q',roleTemplateId:'qa',stationId:'d0-q'})]);
export function createVisualIdentityRegistry(scale:Scale='reference',seeds:readonly VisualActorSeed[]=seedRoles,syntheticStations:readonly SyntheticStation[]=[]){
 const layout=createHybridLayout(scale);
 const floorId='D0-F1';
 const byStation=new Map<string,VisualStation>();const byActor=new Map<string,VisualActor>();const occupiedStations=new Set<string>();const anchors=new Set<string>();
 const add=(s:VisualStation)=>{if(byStation.has(s.stationId)||anchors.has(s.anchor.join(',')))throw new Error('DUPLICATE_STATION_OR_ANCHOR');byStation.set(s.stationId,Object.freeze(s));anchors.add(s.anchor.join(','));};
 for(const s of layout.stations)add({stationId:s.id,floorId,roomId:s.zoneId,departmentId:s.roleTemplate?'d0-dept-'+s.roleTemplate:'d0-dept-reserve',roleTemplateId:s.roleTemplate,anchor:frozenCell(s.anchor),kind:s.activeTemplate?'CORE':'PASSIVE',agentInstanceId:null});
 // Extra anchors are explicit test-only stations, never physical desk or reserve activation claims.
 if(syntheticStations.length>32)throw new Error('SYNTHETIC_STATION_LIMIT');
 const extras=[...syntheticStations];
 for(const s of extras){if(!exact(s,['stationId','roleTemplateId','anchor'])||!idOk(s.stationId)||!s.stationId.startsWith('d0-test-')||!roleOk(s.roleTemplateId)||!Array.isArray(s.anchor)||s.anchor.length!==2||!s.anchor.every(Number.isInteger))throw new Error('INVALID_SYNTHETIC_STATION');}
 extras.sort((a,b)=>a.stationId<b.stationId?-1:a.stationId>b.stationId?1:0);
 for(const s of extras){const roomId=rooms[s.roleTemplateId];const z=layout.zones.find(v=>v.id===roomId)!;const [x,y]=s.anchor;const r=z.rect;
  if(x<r.x||x>=r.x+r.w||y<r.y||y>=r.y+r.h||!hybridWalkable(layout,s.anchor)||!hybridPath(layout,layout.entry,s.anchor)||!hybridPath(layout,layout.briefing,s.anchor)||Object.values(layout.thresholds).some(c=>c[0]===x&&c[1]===y))throw new Error('INVALID_STATION_GEOMETRY');
  add({stationId:s.stationId,floorId,roomId,departmentId:'d0-dept-'+s.roleTemplateId,roleTemplateId:s.roleTemplateId,anchor:frozenCell(s.anchor),kind:'SYNTHETIC_TEST',agentInstanceId:null});
 }
 // Exact descriptor, not a signature; changes to any added station change the revision.
 const layoutRevision=layout.revision+'-A2'+(extras.length?'|TEST|'+JSON.stringify(extras.map(s=>[s.stationId,s.roleTemplateId,s.anchor[0],s.anchor[1]])):'');
 for(const seed of seeds){if(!exact(seed,['visualActorId','roleTemplateId','stationId'])||!idOk(seed.visualActorId)||!seed.visualActorId.startsWith('d0-visual-')||!roleOk(seed.roleTemplateId)||!idOk(seed.stationId))throw new Error('INVALID_ACTOR_SEED');
  if(byActor.has(seed.visualActorId))throw new Error('DUPLICATE_ACTOR');const station=byStation.get(seed.stationId);
  if(!station||station.kind==='PASSIVE'||station.roleTemplateId!==seed.roleTemplateId)throw new Error('STATION_ROLE_OR_REFERENCE');
  if(occupiedStations.has(seed.stationId))throw new Error('STATION_OCCUPIED');occupiedStations.add(seed.stationId);
  byActor.set(seed.visualActorId,Object.freeze({...seed,floorId,roomId:station.roomId,departmentId:station.departmentId,assetProfileId:'d0-asset-'+seed.roleTemplateId,layoutRevision,anchor:station.anchor,agentInstanceId:null}));
 }
 const stations=Object.freeze([...byStation.values()]);const actors=Object.freeze([...byActor.values()]);
 return Object.freeze({mode:'D0_VISUAL_IDENTITY' as const,geometryJoin:'HOLD' as const,authoritative:false as const,placement:false as const,layoutRevision,layout,stations,actors,
  actor:(visualActorId:string)=>byActor.get(visualActorId),station:(stationId:string)=>byStation.get(stationId),
  legacyRole:(role:Role)=>{const matches=actors.filter(a=>a.roleTemplateId===role);return matches.length===1?{status:'RESOLVED' as const,visualActorId:matches[0].visualActorId}:{status:matches.length?'AMBIGUOUS_ROLE' as const:'UNKNOWN_ROLE' as const,visualActorId:null};}
 });
}
