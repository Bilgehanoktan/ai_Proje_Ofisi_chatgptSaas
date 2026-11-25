/** A5R3 read-only D0 view. No runtime join, clock, scene ownership or movement writer. */
import type {createFloorTraffic} from './premiumFloorTraffic';
import type {Layout,Cell} from './premiumHybridLayout';
export type WorldSnapshot=ReturnType<ReturnType<typeof createFloorTraffic>['snapshot']>;
export type WorldReader=Readonly<Pick<ReturnType<typeof createFloorTraffic>,'snapshot'>>;
export const FLOOR_EDGE_MS=240;
const same=(a:Cell,b:Cell)=>a[0]===b[0]&&a[1]===b[1];
export function floorPoint(l:Layout,x:number,y:number){return Object.freeze({x:96+(l.height-1+x-y)*32,y:120+(x+y)*16});}
export function floorCamera(l:Layout,width:number,height:number){if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)throw Error('VIEWPORT_INVALID');const w=(l.width+l.height)*32+192,h=(l.width+l.height)*16+240;return Object.freeze({worldWidth:w,worldHeight:h,zoom:Math.min(width/w,height/h),centerX:w/2,centerY:h/2});}
type Edge=Readonly<{id:string;from:Cell;to:Cell}>;
export function createFloorRenderBridge(reader:WorldReader,initialFloor?:string){
 const read=reader.snapshot.bind(reader);let world=read();
 const check=(s:WorldSnapshot)=>{if(s.mode!=='D0_SYNTHETIC_WORLD'||s.authoritative!==false||s.geometryJoin!=='HOLD'||s.actors.some(a=>a.agentInstanceId!==null))throw Error('D0_VIEW_REQUIRED');};check(world);
 let selected=initialFloor??world.floors[0].floorId;if(!world.floors.some(f=>f.floorId===selected))throw Error('UNKNOWN_VIEW_FLOOR');
 let edge:Edge|null=null,elapsed=FLOOR_EDGE_MS,reduced=false,viewEpoch=0,width=1200,height=800;
 const clear=()=>{edge=null;elapsed=FLOOR_EDGE_MS;};
 const frame=()=>{const f=world.floors.find(f=>f.floorId===selected)!;const actors=world.actors.filter(a=>f.lifecycle==='ACTIVE'&&a.floorId===selected&&!a.inTransit).map(a=>{const e=edge?.id===a.visualActorId&&elapsed<FLOOR_EDGE_MS?edge:null,p=e?elapsed/FLOOR_EDGE_MS:1,x=e?e.from[0]+(e.to[0]-e.from[0])*p:a.cell[0],y=e?e.from[1]+(e.to[1]-e.from[1])*p:a.cell[1];return Object.freeze({id:a.visualActorId,role:a.roleTemplateId,assetProfileId:a.home.assetProfileId,homeStationId:a.home.stationId,cell:a.cell,x,y,point:floorPoint(f.layout,x,y),moving:!!e,atHome:!e&&a.atHome});});
  const navigation=world.floors.map(f=>Object.freeze({floorId:f.floorId,lifecycle:f.lifecycle,visibleActors:world.actors.filter(a=>f.lifecycle==='ACTIVE'&&a.floorId===f.floorId&&!a.inTransit).length,selected:f.floorId===selected}));
  const portals=world.portals.map(p=>Object.freeze({id:p.id,phase:p.phase,cabinFloorId:p.cabinFloorId,queued:p.queue.length,waitReason:p.waitReason,fromFloorId:p.current?.from.floorId??null,toFloorId:p.current?.to.floorId??null,passengerId:p.phase==='TRAVEL'||p.phase==='EXIT'?p.current?.actorId??null:null}));
  return Object.freeze({mode:'D0_FLOOR_RENDER' as const,authoritative:false as const,geometryJoin:'HOLD' as const,revision:world.token.revision,sequence:world.token.sequence,viewEpoch,selectedFloorId:selected,lifecycle:f.lifecycle,trafficStatus:world.status,trafficReason:world.reason,reducedMotion:reduced,interpolating:!!edge&&elapsed<FLOOR_EDGE_MS,camera:floorCamera(f.layout,width,height),layout:f.layout,rooms:f.rooms,stations:f.stations,departments:f.departments,landings:f.landings,navigation:Object.freeze(navigation),actors:Object.freeze(actors),portals:Object.freeze(portals),reservations:Object.freeze(world.reservations.filter(r=>r.cell.startsWith(selected+':')))});
 };
 function capture(){const next=read();check(next);if(next.token.revision!==world.token.revision||next.token.sequence<world.token.sequence||(next.token.sequence===world.token.sequence&&next.token!==world.token))throw Error('WORLD_VIEW_DISCONTINUITY');if(next.token===world.token)return frame();
  if(!next.floors.some(f=>f.floorId===selected))throw Error('VIEW_FLOOR_LOST');const prior=world,finished=!edge||elapsed===FLOOR_EDGE_MS;clear();world=next;
  // Only a contiguous, observed single-cell move may interpolate. Transfer, gap or unfinished edge snaps to observed position.
  if(!reduced&&finished&&next.token.sequence===prior.token.sequence+1&&next.positionsVersion===prior.positionsVersion+1){const changed=next.actors.filter(a=>{const old=prior.actors.find(b=>b.visualActorId===a.visualActorId);return old&&(!same(old.cell,a.cell)||old.floorId!==a.floorId||old.inTransit!==a.inTransit);});if(changed.length===1){const a=changed[0],old=prior.actors.find(b=>b.visualActorId===a.visualActorId)!;if(!old.inTransit&&!a.inTransit&&old.floorId===selected&&a.floorId===selected&&Math.abs(old.cell[0]-a.cell[0])+Math.abs(old.cell[1]-a.cell[1])===1){edge=Object.freeze({id:a.visualActorId,from:old.cell,to:a.cell});elapsed=0;}}}
  return frame();
 }
 function selectFloor(id:string){if(!world.floors.some(f=>f.floorId===id))throw Error('UNKNOWN_VIEW_FLOOR');if(selected!==id){selected=id;viewEpoch++;clear();}return frame();}
 function setViewport(w:number,h:number){floorCamera(world.floors.find(f=>f.floorId===selected)!.layout,w,h);width=w;height=h;return frame();}
 function setReducedMotion(value:boolean){if(typeof value!=='boolean')throw Error('MOTION_FLAG_INVALID');reduced=value;if(reduced)clear();return frame();}
 function advanceVisual(ms:number){if(Number.isFinite(ms)&&ms>0&&edge){elapsed=Math.min(FLOOR_EDGE_MS,elapsed+ms);if(elapsed===FLOOR_EDGE_MS)clear();}return frame();}
 return Object.freeze({capture,frame,selectFloor,setViewport,setReducedMotion,advanceVisual});
}
export type FloorFrame=ReturnType<ReturnType<typeof createFloorRenderBridge>['frame']>;
