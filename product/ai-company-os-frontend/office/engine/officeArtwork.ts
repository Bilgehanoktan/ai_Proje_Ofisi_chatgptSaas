/** Visual-only D0 artwork. Never joins snapshot coordinates or creates agents. */
import {iso,validateDemoLayout,type Floor} from './geometry';
import {roleVisual,roomVisual} from '../../design-system/roleVisuals';
import {reservedDeskDecor} from './stationDecor';
import {reservedDeskAccessories} from './deskAccessories';
import {wallDecorAt} from './wallDecor';
export type Artwork = {ok:true;svg:string;stations:{id:string;role:string;room:string;x:number;y:number}[]}|{ok:false;reason:string};
const esc=(s:string)=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]!));
const pt=(x:number,y:number,z=0)=>{const p=iso(x,y);return [p.x,p.y+26-z];};
const polygon=(points:number[][],fill:string,stroke='#263a50')=>`<polygon points="${points.map(p=>p.join(',')).join(' ')}" fill="${fill}" stroke="${stroke}" stroke-width="1" stroke-linejoin="round"/>`;
const tile=(x:number,y:number,w:number,h:number,z:number,fill:string)=>polygon([pt(x,y,z),pt(x+w,y,z),pt(x+w,y+h,z),pt(x,y+h,z)],fill);
const box=(x:number,y:number,w:number,h:number,height:number,top:string,side:string,base=0)=>polygon([pt(x,y+h,base),pt(x+w,y+h,base),pt(x+w,y+h,base+height),pt(x,y+h,base+height)],side)+polygon([pt(x+w,y,base),pt(x+w,y+h,base),pt(x+w,y+h,base+height),pt(x+w,y,base+height)],'#33465a')+tile(x,y,w,h,base+height,top);
const label=(x:number,y:number,s:string,size=12,fill='#e8eef9')=>`<text x="${x}" y="${y}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="${size}" font-weight="650" fill="${fill}">${esc(s)}</text>`;
export function officeArtwork(raw:Floor,selectedId:string|null=null):Artwork{
 const other=raw.id==='floor-1'?'floor-2':'floor-1';
 const checked=validateDemoLayout({revision:'layout-d3-demo',width:6,height:6,floors:[raw,{id:other,name:'Unused',rooms:[],stations:[],walkable:[]}]});
 if(!checked.ok)return {ok:false,reason:checked.reason};
 const floor=checked.layout.floors[0];
 const pieces:string[]=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 510" role="img" aria-label="Sentetik izometrik ofis; gerçek ajan yok"><defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#17263b"/><stop offset="1" stop-color="#0b1424"/></linearGradient></defs><rect width="900" height="510" rx="14" fill="url(#bg)"/><ellipse cx="450" cy="396" rx="326" ry="52" fill="#080e18" opacity=".6"/>'];
 pieces.push(box(-.5,-.5,6,6,10,'#33475a','#1b2b40',-10));
 for(let x=0;x<6;x++)for(let y=0;y<6;y++){
  const room=floor.rooms.find(r=>x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h);
  pieces.push(tile(x-.5,y-.5,1,1,0,room?.color??((x+y)%2?'#344c60':'#3c566b')));
 }
 // Partial back walls are decorative only; no collision or door semantics.
 for(const r of floor.rooms){
  const x=r.x-.5,y=r.y-.5;
  pieces.push(box(x,y,r.w,.08,31,'#9aabbc','#586e84'));
  pieces.push(box(x,y,.08,Math.min(r.h,.9),31,'#9aabbc','#586e84'));
  // Window bands on the back wall, not physical openings.
  for(let i=0;i<r.w;i++){
   pieces.push(box(x+i+.18,y+.09,.62,.04,13,'#9ad1e4','#4b809e',12));
   // Decorative window sill and mullion; never adds walkable/collision cells.
   pieces.push(box(x+i+.13,y+.10,.72,.08,2,'#d2e0eb','#607b94',9));
   pieces.push(box(x+i+.46,y+.13,.04,.04,13,'#dce7f1','#7893a7',12));
  }
  // Fixed wall-only accents on the last back-wall segment; no occupancy change.
  const wall=pt(x+r.w-.75,y+.12,28);
  pieces.push(wallDecorAt(r.id==='management'||r.id==='quality'?'whiteboard':'wall-shelf',wall[0],wall[1]));
 }
 const stations= [...floor.stations].sort((a,b)=>a.x+a.y-b.x-b.y).map(s=>{
  const p=pt(s.x,s.y),visual=roleVisual(s.role);const color=visual?.accent??'#a9b5c5';const active=s.id===selectedId;
  if(active)pieces.push(`<ellipse cx="${p[0]}" cy="${p[1]}" rx="45" ry="22" fill="none" stroke="#fbe1a0" stroke-width="4"/>`);
  pieces.push(box(s.x-.32,s.y-.32,.65,.45,14,'#d4b18c','#8b6c56'));
  pieces.push(reservedDeskDecor(p[0],p[1],s.agent_instance_id));
  pieces.push(reservedDeskAccessories(p[0],p[1],s.agent_instance_id));
  pieces.push(box(s.x-.10,s.y+.22,.25,.22,9,'#6c819a','#43576e'));
  pieces.push(`<circle cx="${p[0]+29}" cy="${p[1]-22}" r="13" fill="#142338" stroke="${color}" stroke-width="2"/>`,label(p[0]+29,p[1]-18,visual?.initials??'?',10,color));
  return {id:s.id,role:s.role,room:s.room,x:p[0],y:p[1]};
 });
 for(const r of floor.rooms){const p=pt(r.x+r.w-.65,r.y+r.h-.65),v=roomVisual(r.id),accent=v?.accent??'#a9b5c5';pieces.push(`<rect x="${p[0]-53}" y="${p[1]-11}" width="106" height="23" rx="6" fill="#142338" stroke="${accent}"/><rect x="${p[0]-49}" y="${p[1]-7}" width="4" height="15" rx="2" fill="${accent}"/>`,label(p[0]+3,p[1]+4,r.label,12));}
 if(!stations.length){pieces.push(label(450,243,'GENİŞLEME REZERVİ',21),label(450,268,'Aktif oda veya istasyon yok',13,'#bdcadb'));}
 pieces.push(label(450,477,floor.name+' · D0 / REZERV · gerçek ajan yok',14,'#c4d2e6'),'</svg>');
 return {ok:true,svg:pieces.join(''),stations};
}
export function officeImageUri(svg:string){return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);}
