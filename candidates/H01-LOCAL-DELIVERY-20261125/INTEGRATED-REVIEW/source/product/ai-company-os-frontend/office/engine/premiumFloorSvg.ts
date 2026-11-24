/** A5R3 isolated SVG diagnostic renderer, not the native Phaser scene. */
import {floorPoint,type FloorFrame} from './premiumFloorRender';
import type {Rect} from './premiumHybridLayout';
const esc=(s:string)=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]!));
const colors:Record<string,string>={orchestrator:'#f2b865',research:'#60a5fa',engineer:'#49d6bc',qa:'#b9a6fa'};
export function renderFloorSvg(f:FloorFrame):string{
 const l=f.layout,p=(x:number,y:number)=>floorPoint(l,x,y),polygon=(r:Rect)=>[[r.x,r.y],[r.x+r.w,r.y],[r.x+r.w,r.y+r.h],[r.x,r.y+r.h]].map(([x,y])=>{const a=p(x,y);return a.x+','+a.y;}).join(' ');
 const w=f.camera.worldWidth,h=f.camera.worldHeight;const out=[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(f.selectedFloorId)} D0 synthetic floor">`,`<rect width="${w}" height="${h}" fill="#101a29"/>`,`<text x="36" y="46" fill="#e3ebf5" font-size="27" font-family="sans-serif">${esc(f.selectedFloorId)} · ${esc(f.lifecycle)} · D0 / HOLD</text>`];
 out.push(`<polygon points="${polygon({x:0,y:0,w:l.width,h:l.height})}" fill="#253448" stroke="#6b819a" stroke-width="2"/>`);
 for(const z of l.zones){const reserve=z.kind==='RESERVED_POD'||z.kind==='FLOOR_PORTAL';out.push(`<polygon points="${polygon(z.rect)}" fill="${reserve?'#384456':'#344e61'}" fill-opacity="${reserve?.55:.72}" stroke="#7890a8" stroke-width="1"${reserve?' stroke-dasharray="8 5"':''}/>`);const c=p(z.rect.x+z.rect.w/2,z.rect.y+z.rect.h/2);out.push(`<text x="${c.x}" y="${c.y}" fill="#b4c7da" font-size="15" text-anchor="middle" font-family="sans-serif">${esc(z.id)}</text>`);}
 const draw:{depth:number;markup:string}[]=[];
 for(const item of l.footprints){const r=item.rect,c=p(r.x+r.w/2,r.y+r.h/2);draw.push({depth:c.y,markup:`<polygon points="${polygon(r)}" fill="${item.kind==='partition'?'#6f99ad':'#c2a27d'}" stroke="#17283a" stroke-width="2"/>`});}
 for(const s of f.stations){const c=p(s.anchor[0],s.anchor[1]);draw.push({depth:c.y,markup:`<ellipse cx="${c.x}" cy="${c.y}" rx="13" ry="7" fill="none" stroke="${s.kind==='PASSIVE'?'#64748b':'#a6c6e1'}" stroke-width="2"/>`});}
 for(const a of f.actors){const {x,y}=a.point,c=colors[a.role]??'#cbd5e1';draw.push({depth:y,markup:`<g data-actor="${esc(a.id)}"><ellipse cx="${x}" cy="${y}" rx="12" ry="5" fill="#0b1420" opacity=".6"/><rect x="${x-8}" y="${y-27}" width="16" height="25" rx="5" fill="${c}"/><circle cx="${x}" cy="${y-33}" r="8" fill="#e4bc96"/><title>${esc(a.id)}</title></g>`});}
 draw.sort((a,b)=>a.depth-b.depth);out.push(...draw.map(a=>a.markup));
 for(const c of f.landings){const q=p(c[0],c[1]);out.push(`<circle cx="${q.x}" cy="${q.y}" r="7" fill="none" stroke="#f2b865" stroke-width="2"/>`);}
 for(const r of f.reservations){const [x,y]=r.cell.slice(f.selectedFloorId.length+1).split(',').map(Number),q=p(x,y);out.push(`<circle cx="${q.x}" cy="${q.y}" r="11" fill="none" stroke="#f97316" stroke-width="3"/>`);}
 out.push(`<text x="36" y="${h-55}" fill="#d3deeb" font-family="sans-serif" font-size="20">Visible actors: ${f.actors.length} · Sequence: ${f.sequence} · ${esc(f.trafficStatus)}</text>`);
 const summary=f.portals.map(p=>`${p.id}: ${p.phase}${p.passengerId?' / '+p.passengerId:''}`).join(' | ');out.push(`<text x="36" y="${h-25}" fill="#9eb3c9" font-family="sans-serif" font-size="16">${esc(summary)}</text></svg>`);return out.join('\n');
}
