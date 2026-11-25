// D0 synthetic geometry only. No placement, movement authority or runtime evidence.
export type Point = [number,number];
export type Room = {id:string;label:string;x:number;y:number;w:number;h:number;color:string};
export type Station = {id:string;role:string;room:string;x:number;y:number;agent_instance_id:null};
export type Floor = {id:string;name:string;rooms:Room[];stations:Station[];walkable:number[][]};
export type DemoLayout = {revision:'layout-d3-demo';width:6;height:6;floors:Floor[]};
export type LayoutCheck = {ok:true;layout:DemoLayout}|{ok:false;reason:string};
export const iso = (x:number,y:number) => ({x:450+(x-y)*51,y:105+(x+y)*26});
export const pointKey = (p:readonly number[]) => p.join(',');
const obj = (x:unknown): x is Record<string,unknown> => typeof x==='object' && x!==null && !Array.isArray(x);
const text = (x:unknown): x is string => typeof x==='string' && x.trim().length>0 && x.length<=120;
const cell = (x:unknown): x is number => typeof x==='number' && Number.isInteger(x) && x>=0 && x<6;
const size = (x:unknown): x is number => typeof x==='number' && Number.isInteger(x) && x>0 && x<=6;
const point = (p:unknown): p is Point => Array.isArray(p) && p.length===2 && cell(p[0]) && cell(p[1]);
const fail = (reason:string): LayoutCheck => ({ok:false,reason});

// Strictly scoped to the existing demo fixture. This is not canonical layout acceptance.
export function validateDemoLayout(raw:unknown):LayoutCheck {
 if(!obj(raw)||raw.revision!=='layout-d3-demo'||raw.width!==6||raw.height!==6||!Array.isArray(raw.floors)||raw.floors.length!==2) return fail('LAYOUT_SCOPE_INVALID');
 const floors:Floor[]=[]; const floorIds=new Set<string>(); const stationIds=new Set<string>();
 for(const f of raw.floors){
  if(!obj(f)||!text(f.id)||!['floor-1','floor-2'].includes(f.id)||floorIds.has(f.id)||!text(f.name)||!Array.isArray(f.rooms)||!Array.isArray(f.stations)||!Array.isArray(f.walkable)||f.rooms.length>36||f.stations.length>36||f.walkable.length>36) return fail('FLOOR_INVALID');
  floorIds.add(f.id);
  const rooms:Room[]=[]; const roomCells=new Map<string,Set<string>>(); const occupied=new Set<string>();
  for(const r of f.rooms){
   if(!obj(r)||!text(r.id)||roomCells.has(r.id)||!text(r.label)||!cell(r.x)||!cell(r.y)||!size(r.w)||!size(r.h)||r.x+r.w>6||r.y+r.h>6||typeof r.color!=='string'||!/^#[0-9a-fA-F]{6}$/.test(r.color)) return fail('ROOM_INVALID');
   const cells=new Set<string>();
   for(let x=r.x;x<r.x+r.w;x++)for(let y=r.y;y<r.y+r.h;y++){
    const k=pointKey([x,y]);if(occupied.has(k)) return fail('ROOM_OVERLAP');occupied.add(k);cells.add(k);
   }
   roomCells.set(r.id,cells);rooms.push({id:r.id,label:r.label,x:r.x,y:r.y,w:r.w,h:r.h,color:r.color});
  }
  const stations:Station[]=[];const positions=new Set<string>();
  for(const s of f.stations){
   if(!obj(s)||!text(s.id)||stationIds.has(s.id)||!text(s.role)||!text(s.room)||!cell(s.x)||!cell(s.y)||s.agent_instance_id!==null) return fail('STATION_INVALID');
   const k=pointKey([s.x,s.y]);if(positions.has(k)||!roomCells.get(s.room)?.has(k)) return fail('STATION_GEOMETRY_INVALID');
   stationIds.add(s.id);positions.add(k);stations.push({id:s.id,role:s.role,room:s.room,x:s.x,y:s.y,agent_instance_id:null});
  }
  const walkable:Point[]=[];const seen=new Set<string>();
  for(const p of f.walkable){
   if(!point(p)||seen.has(pointKey(p))||positions.has(pointKey(p)))return fail('WALKABLE_INVALID');
   seen.add(pointKey(p));walkable.push([p[0],p[1]]);
  }
  if(f.id==='floor-2'&&(stations.length||rooms.length))return fail('RESERVE_NOT_EMPTY');
  floors.push({id:f.id,name:f.name,rooms,stations,walkable});
 }
 return {ok:true,layout:{revision:'layout-d3-demo',width:6,height:6,floors}};
}
export function route(floor:Floor,start:Point,end:Point):Point[]|null{
 if(!point(start)||!point(end))return null;
 const blocked=new Set(floor.stations.map(s=>pointKey([s.x,s.y])));
 const allowed=new Set(floor.walkable.filter(p=>point(p)&&!blocked.has(pointKey(p))).map(pointKey));
 if(!allowed.has(pointKey(start))||!allowed.has(pointKey(end)))return null;
 const queue:Point[]=[start],seen=new Map<string,Point|null>([[pointKey(start),null]]);
 for(let i=0;i<queue.length;i++){
  const p=queue[i];if(pointKey(p)===pointKey(end)){const result:Point[]=[];let cursor:Point|null=p;while(cursor){result.unshift(cursor);cursor=seen.get(pointKey(cursor))??null;}return result;}
  for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){const next:Point=[p[0]+dx,p[1]+dy];const k=pointKey(next);if(allowed.has(k)&&!seen.has(k)){seen.set(k,p);queue.push(next);}}
 }return null;
}
// Distance is in path segments, not wall-clock or agent state.
export function markerPosition(path:readonly Point[],distance:number):{x:number;y:number}|null{
 if(!path.length||!Number.isFinite(distance))return null;
 const d=Math.max(0,Math.min(path.length-1,distance));const i=Math.floor(d);const a=path[i],b=path[Math.min(i+1,path.length-1)];
 const p=iso(a[0]+(b[0]-a[0])*(d-i),a[1]+(b[1]-a[1])*(d-i));return {x:p.x,y:p.y+26};
}
export function cameraView(zoom:number,x:number,y:number){
 const z=Number.isFinite(zoom)?Math.max(.75,Math.min(1.45,zoom)):1;
 // Constrain the center; at zoom <= 1 the entire logical scene stays centered.
 const dx=Math.max(0,(900-900/z)/2),dy=Math.max(0,(510-510/z)/2);
 return {zoom:z,x:450+Math.max(-dx,Math.min(dx,Number.isFinite(x)?x:0)),y:255+Math.max(-dy,Math.min(dy,Number.isFinite(y)?y:0))};
}
export function avatarProjection(instanceId:string|null,freshness:string,state:string,proof:boolean):string{
 if(!instanceId)return 'RESERVED';
 if(freshness!=='CURRENT')return 'UNKNOWN';
 if(state==='APPROVAL_REQUESTED')return 'WAITING_APPROVAL';
 if(state==='BLOCKED'||state==='REVOKED')return 'BLOCKED';
 if(state==='COMPLETED'||proof)return 'UNVERIFIED';
 return 'UNKNOWN';
}
