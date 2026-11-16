/** DEC-28C-D candidate geometry; presentation-only, never a canonical placement. */
export type Cell = readonly [number, number];
export type Rect = Readonly<{x:number;y:number;w:number;h:number}>;
export type Role = 'orchestrator'|'research'|'engineer'|'qa';
export type Scale = 'compact'|'reference'|'expanded';
export type ZoneKind = 'SEMI_OPEN_POD'|'COMMAND_HUB'|'OPEN_CIRCULATION'|'SIDE_CIRCULATION'|'RESERVED_POD'|'MEETING_ZONE'|'SEMI_ENCLOSED_POD'|'ENTRY_THRESHOLD'|'FLOOR_PORTAL';
export type Zone = Readonly<{id:string;kind:ZoneKind;rect:Rect}>;
export type Footprint = Readonly<{id:string;zoneId:string;kind:'desk'|'table'|'partition';rect:Rect}>;
export type Station = Readonly<{id:string;zoneId:string;roleTemplate:Role|null;anchor:Cell;activeTemplate:boolean;agentInstanceId:null}>;
export type Layout = Readonly<{revision:string;scale:Scale;width:number;height:number;tile:32;mode:'D0_GEOMETRY_CANDIDATE';geometryJoin:'HOLD';zones:readonly Zone[];footprints:readonly Footprint[];stations:readonly Station[];entry:Cell;entryInterior:Cell;briefing:Cell;thresholds:Readonly<Record<Role,Cell>>;portal:Readonly<{zoneId:string;anchor:Cell;enabled:false;targetFloorId:null}>}>;
const dimensions = {compact:[40,26],reference:[48,30],expanded:[56,34]} as const;
const templates:readonly [string,ZoneKind,number,number,number,number][] = [
 ['F1-RSCH','SEMI_OPEN_POD',2,2,14,11],['F1-ORCH','COMMAND_HUB',20,5,27,12],['F1-ENG','SEMI_OPEN_POD',33,2,45,11],
 ['F1-COR','OPEN_CIRCULATION',2,13,45,19],['F1-VL','SIDE_CIRCULATION',15,2,19,28],['F1-VR','SIDE_CIRCULATION',28,2,32,28],
 ['F1-EXP','RESERVED_POD',2,21,14,27],['F1-BRIEF','MEETING_ZONE',20,21,27,26],['F1-QA','SEMI_ENCLOSED_POD',33,21,45,27],
 ['F1-ENTRY','ENTRY_THRESHOLD',23,27,25,29],['F1-PORTAL','FLOOR_PORTAL',29,27,31,28]
];
// Inclusive DEC coordinates; collision rectangles use half-open edges instead.
const rect=(x:number,y:number,x1:number,y1:number):Rect=>({x,y,w:x1-x+1,h:y1-y+1});
const contains=(r:Rect,c:Cell)=>c[0]>=r.x&&c[0]<r.x+r.w&&c[1]>=r.y&&c[1]<r.y+r.h;
const overlap=(a:Rect,b:Rect)=>a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;
const inside=(a:Rect,b:Rect)=>contains(b,[a.x,a.y])&&contains(b,[a.x+a.w-1,a.y+a.h-1]);
const same=(a:Cell,b:Cell)=>a[0]===b[0]&&a[1]===b[1];
const deepFreeze=<T>(v:T):T=>{if(v&&typeof v==='object'){for(const child of Object.values(v))deepFreeze(child);Object.freeze(v);}return v;};
export function createHybridLayout(scale:Scale='reference'):Layout {
 if(!Object.prototype.hasOwnProperty.call(dimensions,scale))throw new Error('UNKNOWN_SCALE');
 const [width,height]=dimensions[scale];const sx=(x:number)=>Math.floor(x*width/48),sy=(y:number)=>Math.floor(y*height/30);
 const mapRect=(r:Rect):Rect=>({x:sx(r.x),y:sy(r.y),w:sx(r.x+r.w)-sx(r.x),h:sy(r.y+r.h)-sy(r.y)});
 const cell=(x:number,y:number):Cell=>[sx(x),sy(y)];
 const zones=templates.map(([id,kind,x,y,x1,y1])=>({id,kind,rect:mapRect(rect(x,y,x1,y1))}));
 const footprints:Footprint[]=[];
 const add=(id:string,zoneId:string,kind:Footprint['kind'],x:number,y:number,x1:number,y1:number)=>{footprints.push({id,zoneId,kind,rect:mapRect(rect(x,y,x1,y1))});};
 add('r-desk','F1-RSCH','desk',7,6,9,6);add('o-desk','F1-ORCH','desk',23,8,25,8);add('e-desk','F1-ENG','desk',38,6,40,6);add('q-desk','F1-QA','desk',38,25,40,25);
 add('brief-table','F1-BRIEF','table',21,22,22,24);add('reserve-desk-1','F1-EXP','desk',5,23,7,23);add('reserve-desk-2','F1-EXP','desk',9,23,11,23);
 // Low/transparent partitions are physical footprints; door gaps remain open.
 add('r-north','F1-RSCH','partition',2,2,14,2);add('r-west','F1-RSCH','partition',2,3,2,11);
 add('r-east-top','F1-RSCH','partition',14,3,14,7);add('r-east-bottom','F1-RSCH','partition',14,9,14,11);
 add('e-north','F1-ENG','partition',33,2,45,2);add('e-east','F1-ENG','partition',45,3,45,11);
 add('e-west-top','F1-ENG','partition',33,3,33,7);add('e-west-bottom','F1-ENG','partition',33,9,33,11);
 add('q-north','F1-QA','partition',33,21,45,21);add('q-south','F1-QA','partition',33,27,45,27);add('q-east','F1-QA','partition',45,22,45,26);
 add('q-west-top','F1-QA','partition',33,22,33,22);add('q-west-bottom','F1-QA','partition',33,24,33,26);
 const station=(id:string,zoneId:string,roleTemplate:Role|null,x:number,y:number):Station=>({id,zoneId,roleTemplate,anchor:cell(x,y),activeTemplate:roleTemplate!==null,agentInstanceId:null});
 const layout:Layout={revision:`D0-HYBRID-A1-${scale}-r1`,scale,width,height,tile:32,mode:'D0_GEOMETRY_CANDIDATE',geometryJoin:'HOLD',zones,footprints,stations:[station('d0-r','F1-RSCH','research',8,7),station('d0-o','F1-ORCH','orchestrator',24,9),station('d0-e','F1-ENG','engineer',39,7),station('d0-q','F1-QA','qa',39,24),station('d0-reserve-1','F1-EXP',null,6,24),station('d0-reserve-2','F1-EXP',null,10,24)],entry:[sx(24),height-1],entryInterior:cell(24,28),briefing:cell(24,23),thresholds:{research:cell(14,8),orchestrator:cell(24,12),engineer:cell(33,8),qa:cell(33,23)},portal:{zoneId:'F1-PORTAL',anchor:cell(30,28),enabled:false,targetFloorId:null}};
 const errors=validateHybridLayout(layout);if(errors.length)throw new Error(errors.join(';'));return deepFreeze(layout);
}
export function hybridWalkable(l:Layout,c:Cell):boolean{
 const [x,y]=c;if(!Number.isInteger(x)||!Number.isInteger(y)||x<0||y<0||x>=l.width||y>=l.height)return false;
 const entry=l.zones.find(z=>z.id==='F1-ENTRY');
 if((x===0||x===l.width-1||y===0||y===l.height-1)&&!(y===l.height-1&&entry&&contains(entry.rect,c)))return false;
 return !l.zones.some(z=>(z.kind==='RESERVED_POD'||z.kind==='FLOOR_PORTAL')&&contains(z.rect,c))&&!l.footprints.some(f=>contains(f.rect,c));
}
/** Single-cell static reachability only. No live movement or concurrency claims. */
export function hybridPath(l:Layout,from:Cell,to:Cell):Cell[]|null{
 if(!hybridWalkable(l,from)||!hybridWalkable(l,to))return null;
 const key=(c:Cell)=>c.join(','),q:Cell[]=[[...from]],prev=new Map<string,Cell|null>([[key(from),null]]);
 for(let i=0;i<q.length;i++){const c=q[i];if(same(c,to)){const out:Cell[]=[];let n:Cell|null=c;while(n){out.unshift(n);n=prev.get(key(n))??null;}return out;}
 for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){const n:Cell=[c[0]+dx,c[1]+dy];if(!prev.has(key(n))&&hybridWalkable(l,n)){prev.set(key(n),c);q.push(n);}}}return null;
}
const permittedZoneOverlap=(a:Zone,b:Zone)=>{const ids=[a.id,b.id].sort().join('|');return ['F1-COR|F1-VL','F1-COR|F1-VR','F1-PORTAL|F1-VR'].includes(ids);};
/** Validator for typed local candidates, not an untrusted external schema parser. */
export function validateHybridLayout(l:Layout):string[]{
 const errors:string[]=[];const unique=(ids:readonly string[])=>new Set(ids).size===ids.length;
 if(!Object.prototype.hasOwnProperty.call(dimensions,l.scale)||l.width!==dimensions[l.scale][0]||l.height!==dimensions[l.scale][1]||l.tile!==32||l.mode!=='D0_GEOMETRY_CANDIDATE'||l.geometryJoin!=='HOLD'||l.revision!==`D0-HYBRID-A1-${l.scale}-r1`)return ['SCOPE_OR_DIMENSION'];
 const bounds:Rect={x:0,y:0,w:l.width,h:l.height};const valid=(r:Rect)=>[r.x,r.y,r.w,r.h].every(Number.isInteger)&&r.w>0&&r.h>0&&inside(r,bounds);
 if(!unique(l.zones.map(z=>z.id))||l.zones.length!==templates.length||templates.some(([id,kind])=>!l.zones.some(z=>z.id===id&&z.kind===kind)))errors.push('ZONE_ID_KIND');
 for(const [i,z] of l.zones.entries()){if(!valid(z.rect))errors.push('ZONE_BOUNDS:'+z.id);for(const b of l.zones.slice(i+1))if(overlap(z.rect,b.rect)&&!permittedZoneOverlap(z,b))errors.push('ZONE_OVERLAP:'+z.id+':'+b.id);}
 const requiredFootprints=['r-desk','o-desk','e-desk','q-desk','brief-table','reserve-desk-1','reserve-desk-2','r-north','r-west','r-east-top','r-east-bottom','e-north','e-east','e-west-top','e-west-bottom','q-north','q-south','q-east','q-west-top','q-west-bottom'];
 if(!unique(l.footprints.map(f=>f.id))||l.footprints.length!==requiredFootprints.length||requiredFootprints.some(id=>!l.footprints.some(f=>f.id===id)))errors.push('FOOTPRINT_ID');
 for(const [i,f] of l.footprints.entries()){const z=l.zones.find(z=>z.id===f.zoneId);if(!z||!valid(f.rect)||!inside(f.rect,z.rect))errors.push('FOOTPRINT_BOUNDS:'+f.id);if(l.footprints.slice(i+1).some(b=>overlap(f.rect,b.rect)))errors.push('FOOTPRINT_OVERLAP:'+f.id);}
 const active=l.stations.filter(s=>s.activeTemplate);const expected:Record<Role,string>={research:'F1-RSCH',orchestrator:'F1-ORCH',engineer:'F1-ENG',qa:'F1-QA'};
 if(!unique(l.stations.map(s=>s.id))||!unique(l.stations.map(s=>s.anchor.join(',')))||l.stations.length!==6||active.length!==4||Object.entries(expected).some(([r,z])=>active.filter(s=>s.roleTemplate===r&&s.zoneId===z).length!==1))errors.push('STATION_SET');
 for(const s of l.stations){const z=l.zones.find(z=>z.id===s.zoneId);if(!z||!s.anchor.every(Number.isInteger)||!contains(z.rect,s.anchor)||s.agentInstanceId!==null||(!s.activeTemplate&&(s.roleTemplate!==null||s.zoneId!=='F1-EXP'||hybridWalkable(l,s.anchor)))||(s.activeTemplate&&!hybridWalkable(l,s.anchor)))errors.push('STATION_SCOPE:'+s.id);}
 const portal=l.zones.find(z=>z.id===l.portal.zoneId);if(l.portal.enabled!==false||l.portal.targetFloorId!==null||portal?.kind!=='FLOOR_PORTAL'||!contains(portal.rect,l.portal.anchor)||hybridWalkable(l,l.portal.anchor))errors.push('PORTAL_SCOPE');
 const entrance=l.zones.find(z=>z.id==='F1-ENTRY'),brief=l.zones.find(z=>z.id==='F1-BRIEF');
 if(!entrance||!brief||!contains(entrance.rect,l.entry)||l.entry[1]!==l.height-1||!contains(entrance.rect,l.entryInterior)||!contains(brief.rect,l.briefing)||!hybridPath(l,l.entry,l.entryInterior)||!hybridPath(l,l.entryInterior,l.briefing))errors.push('ENTRY_BRIEFING_PATH');
 for(const s of active){const role=s.roleTemplate;if(!role||!Object.prototype.hasOwnProperty.call(expected,role)){errors.push('STATION_ROLE:'+s.id);continue;}const threshold=l.thresholds[role],zone=l.zones.find(z=>z.id===s.zoneId);if(!threshold||!zone||!contains(zone.rect,threshold)||!hybridPath(l,l.entry,threshold)||!hybridPath(l,threshold,s.anchor)||!hybridPath(l,l.briefing,s.anchor))errors.push('STATION_PATH:'+s.id);}
 return errors;
}
export function compareHybridLayouts(){return (['compact','reference','expanded'] as const).map(scale=>{let l:Layout;try{l=createHybridLayout(scale);}catch(error){return {scale,width:dimensions[scale][0],height:dimensions[scale][1],status:'REJECTED_GEOMETRY' as const,reason:error instanceof Error?error.message:'UNKNOWN_ERROR'};}let walkable=0,clear2x2=0;for(let y=0;y<l.height;y++)for(let x=0;x<l.width;x++){if(hybridWalkable(l,[x,y]))walkable++;if([[x,y],[x+1,y],[x,y+1],[x+1,y+1]].every(c=>hybridWalkable(l,c as [number,number])))clear2x2++;}return {scale,width:l.width,height:l.height,status:'STATIC_PATH_PASS' as const,walkable,clear2x2,entryPaths:Object.fromEntries(l.stations.filter(s=>s.activeTemplate).map(s=>[s.roleTemplate,hybridPath(l,l.entry,s.anchor)!.length-1])),briefingPaths:Object.fromEntries(l.stations.filter(s=>s.activeTemplate).map(s=>[s.roleTemplate,hybridPath(l,l.briefing,s.anchor)!.length-1]))};});}
