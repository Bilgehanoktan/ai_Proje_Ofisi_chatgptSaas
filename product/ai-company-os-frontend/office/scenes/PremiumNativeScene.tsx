'use client';
import {useEffect,useRef,useState} from 'react';
import {advance,command,furniture,initialActors,iso,position,roles,rooms,WIDTH,HEIGHT,routeStatus,type Role,type Mode} from '../engine/premiumModel';
import {drawAvatar,drawFurnitureCell} from './premiumArt';
import {cameraViewport} from '../engine/premiumRouting';
import {inspectOfficeV0} from '../engine/premiumOfficeV0';
import snapshot from '../../fixtures/office.snapshot.json';
import {useProjectionRead} from '../../features/data/useProjectionRead';

type Status='loading'|'ready'|'unavailable';
const modes:Mode[]=['idle','work','meeting','rest'];
const labels:Record<Mode,string>={idle:'Bekleme',work:'Çalışma',meeting:'Toplantı',rest:'Dinlenme'};
const map={x:842,y:16,w:242,h:158} as const;
export default function PremiumNativeScene(){
 const host=useRef<HTMLDivElement>(null),actors=useRef(initialActors()),selection=useRef<Role>('orchestrator'),floorRef=useRef(1),paused=useRef(false),reduced=useRef(true);
 const [status,setStatus]=useState<Status>('loading'),[floor,setFloor]=useState(1),[role,setRole]=useState<Role>('orchestrator'),[pause,setPause]=useState(false),[notice,setNotice]=useState('Dekoratif rol seçin.'),[motionReduced,setMotionReduced]=useState(true);
 const [routing,setRouting]=useState('READY'),[cameraView,setCameraView]=useState({x:0,y:0,w:1100,h:720,zoom:1});
 const [visualRoles,setVisualRoles]=useState(()=>initialActors().map(a=>({role:a.role,mode:a.mode,cell:a.cell.join(','),moving:false})));
 const cameraAction=useRef<(action:'in'|'out'|'reset'|'focus')=>void>(()=>{});
 const historical=useProjectionRead('office-workbench'),source=inspectOfficeV0(snapshot);
 useEffect(()=>{const mq=window.matchMedia('(prefers-reduced-motion: reduce)');const sync=()=>{reduced.current=mq.matches;setMotionReduced(mq.matches);};sync();mq.addEventListener('change',sync);return()=>mq.removeEventListener('change',sync);},[]);
 useEffect(()=>{let disposed=false;let game:import('phaser').Game|undefined;setStatus('loading');const timeout=window.setTimeout(()=>{if(!disposed){disposed=true;game?.destroy(true);cameraAction.current=()=>{};setStatus('unavailable');}},10000);
 import('phaser').then(({default:P})=>{if(disposed||!host.current)return;
 const scene={create(this:import('phaser').Scene){
  if(disposed)return;
  const active=this.add.container(0,0),reserve=this.add.container(0,0).setVisible(false);
  const tile=(g:import('phaser').GameObjects.Graphics,x:number,y:number,color:number)=>{const p=iso(x,y);const points=[{x:p.x,y:p.y-18},{x:p.x+36,y:p.y},{x:p.x,y:p.y+18},{x:p.x-36,y:p.y}];g.fillStyle(color).fillPoints(points,true).lineStyle(1,0x8798a3,.4).strokePoints(points,true);};
  for(const [layer,empty] of [[active,false],[reserve,true]] as const){const g=this.add.graphics();layer.add(g);g.setDepth(-100);for(let x=0;x<WIDTH;x++)for(let y=0;y<HEIGHT;y++){const r=!empty&&rooms.find(r=>x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h);tile(g,x,y,r?r.color:(x+y)%2?0x344554:0x3d4f60);}}
  // Glass accents remain decorative and behind walkable/furniture objects.
  for(const r of rooms){const a=iso(r.x,r.y),b=iso(r.x+r.w-1,r.y);const glass=this.add.graphics();glass.fillStyle(0x88b3c4,.22).fillPoints([{x:a.x-36,y:a.y},{x:b.x+36,y:b.y},{x:b.x+36,y:b.y-53},{x:a.x-36,y:a.y-53}],true).lineStyle(2,0x7898a8,.9).lineBetween(a.x-36,a.y-53,b.x+36,b.y-53);for(let i=0;i<=r.w;i++){const t=i/r.w,x=a.x-36+(b.x-a.x+72)*t,y=a.y+(b.y-a.y)*t;glass.lineBetween(x,y,x,y-53);}glass.setDepth(-50);active.add(glass);}
  rooms.forEach(r=>{const p=iso(r.x,r.y);const label=this.add.text(p.x,p.y-58,r.name,{fontSize:'13px',color:'#e8e3db',backgroundColor:'#18202c',padding:{x:5,y:3}}).setOrigin(.5).setDepth(2e6);active.add(label);});
  for(const f of furniture)for(let x=f.x;x<f.x+f.w;x++)for(let y=f.y;y<f.y+f.h;y++){const g=this.add.graphics();active.add(g);drawFurnitureCell(g,f,x,y);}
  const rigs=roles.map(r=>{const g=this.add.graphics();active.add(g);return {role:r,g};});
  const emptyLabel=this.add.text(550,520,'KAT 2 · PASİF GENİŞLEME REZERVİ',{fontSize:'20px',color:'#b6c7d7'}).setOrigin(.5);reserve.add(emptyLabel);
  const cam=this.cameras.main;cam.setBounds(0,0,1100,720);cam.centerOn(550,360);
  // Native second camera observes the same scene; no DOM/canvas screenshot or synthetic map clone.
  const mini=this.cameras.add(map.x,map.y,map.w,map.h).setName('premium-minimap').setZoom(.19).setBackgroundColor('#111c28');mini.centerOn(550,360);
  const marker=this.add.graphics().setDepth(3e6);cam.ignore(marker);
  const inMap=(x:number,y:number)=>x>=map.x&&x<map.x+map.w&&y>=map.y&&y<map.y+map.h;
  this.input.addPointer(1);
  const fingers=new Map<number,{x:number;y:number}>();
  const zoomAt=(x:number,y:number,z:number)=>{const old=cam.getWorldPoint(x,y);cam.setZoom(P.Math.Clamp(z,1,2.4));cam.preRender();const next=cam.getWorldPoint(x,y);cam.scrollX+=old.x-next.x;cam.scrollY+=old.y-next.y;};
  const pan=(dx:number,dy:number)=>{cam.scrollX-=dx/cam.zoom;cam.scrollY-=dy/cam.zoom;};
  this.input.on('pointerdown',(p:import('phaser').Input.Pointer)=>{if(p.button!==0)return;if(inMap(p.x,p.y)){if(!fingers.size){const pt=mini.getWorldPoint(p.x,p.y);cam.centerOn(P.Math.Clamp(pt.x,0,1100),P.Math.Clamp(pt.y,0,720));}return;}if(fingers.size<2)fingers.set(p.id,{x:p.x,y:p.y});});
  this.input.on('pointermove',(p:import('phaser').Input.Pointer)=>{const prev=fingers.get(p.id);if(!prev||!p.isDown)return;const next={x:p.x,y:p.y};if(fingers.size===2){const other=[...fingers.entries()].find(([id])=>id!==p.id)?.[1];if(other){const before=Math.hypot(prev.x-other.x,prev.y-other.y),after=Math.hypot(next.x-other.x,next.y-other.y);if(before>4&&after>4){zoomAt((prev.x+other.x)/2,(prev.y+other.y)/2,cam.zoom*after/before);pan((next.x-prev.x)/2,(next.y-prev.y)/2);}}}else pan(next.x-prev.x,next.y-prev.y);fingers.set(p.id,next);});
  const release=(p:import('phaser').Input.Pointer)=>{fingers.delete(p.id);};this.input.on('pointerup',release);this.input.on('pointerupoutside',release);this.input.on('gameout',()=>{fingers.clear();});
  this.input.on('wheel',(p:import('phaser').Input.Pointer,_over:unknown,_dx:number,dy:number)=>{if(!fingers.size&&!inMap(p.x,p.y))zoomAt(p.x,p.y,cam.zoom*Math.exp(-dy*.0015));});
  cameraAction.current=a=>{if(a==='reset'){cam.setZoom(1);cam.centerOn(550,360);}else if(a==='focus'){const actor=actors.current.find(v=>v.role===selection.current);if(actor&&floorRef.current===1){const p=position(actor);cam.setZoom(1.6);cam.centerOn(p.x,p.y);}}else cam.setZoom(P.Math.Clamp(cam.zoom+(a==='in'?.2:-.2),1,2.4));};
  let lastReadback=-Infinity;
  this.events.on('update',(time:number,delta:number)=>{if(disposed)return;active.setVisible(floorRef.current===1);reserve.setVisible(floorRef.current===2);
   const view=cameraViewport(cam.scrollX,cam.scrollY,cam.width,cam.height,cam.zoom);marker.clear().lineStyle(10,0x86e9e0,.95).strokeRect(view.x,view.y,view.w,view.h);
   if(time-lastReadback>=250)setCameraView({...view,zoom:cam.zoom});
   if(floorRef.current!==1){if(time-lastReadback>=250)lastReadback=time;return;}if(!paused.current&&!reduced.current)advance(actors.current,delta/1000);
   for(const rig of rigs){const a=actors.current.find(v=>v.role===rig.role)!;drawAvatar(rig.g,a,time,!paused.current&&!reduced.current,a.role===selection.current);}
   active.sort('depth');if(time-lastReadback>=250){lastReadback=time;setRouting(routeStatus(actors.current));setVisualRoles(actors.current.map(a=>({role:a.role,mode:a.mode,cell:a.cell.join(','),moving:a.progress>0})));}});
  window.clearTimeout(timeout);if(!disposed)setStatus('ready');
 }};
 game=new P.Game({type:P.AUTO,width:1100,height:720,parent:host.current,backgroundColor:'#131b27',scale:{mode:P.Scale.FIT,autoCenter:P.Scale.CENTER_BOTH},scene});
 }).catch(()=>{window.clearTimeout(timeout);if(!disposed){disposed=true;game?.destroy(true);setStatus('unavailable');}});
 return()=>{window.clearTimeout(timeout);if(!disposed){disposed=true;game?.destroy(true);}cameraAction.current=()=>{};};},[]);
 function select(r:Role){selection.current=r;setRole(r);cameraAction.current('focus');}
 function changeFloor(n:number){floorRef.current=n;setFloor(n);cameraAction.current('reset');}
 return <section aria-label="Native premium ofis"><p className="notice" role="status">D0 · JOIN_HOLD · Dekoratif rol şablonları, gerçek ajan veya görev yok. {status}</p><div className="chips"><button aria-pressed={floor===1} onClick={()=>changeFloor(1)}>Kat 1</button><button aria-pressed={floor===2} onClick={()=>changeFloor(2)}>Kat 2 · Rezerv</button>{(['out','reset','in','focus'] as const).map(a=><button key={a} disabled={status!=='ready'||(a==='focus'&&floor!==1)} onClick={()=>cameraAction.current(a)}>{({out:'−',reset:'Sıfırla',in:'+',focus:'Ajanı odakla'})[a]}</button>)}</div><div ref={host} style={{width:'100%',aspectRatio:'1100 / 720',touchAction:'none',background:'#131b27'}} aria-hidden="true"/>{status!=='ready'&&<p role="status">{status==='loading'?'Motor yükleniyor…':'Phaser kullanılamıyor. '}<a href="/office/premium">Gömülü ofis önizlemesi ↗</a></p>}<p data-camera-view={JSON.stringify(cameraView)}>Mini harita · sağ üst köşedeki konuma dokunarak kamerayı merkezle.</p><div className="chips">{roles.map(r=><button key={r} disabled={floor!==1} aria-pressed={role===r} onClick={()=>select(r)}>{r}</button>)}</div><div className="chips">{modes.map(m=><button key={m} disabled={status!=='ready'||floor!==1||motionReduced} onClick={()=>setNotice(command(actors.current,role,m)?'Dekoratif komut kabul edildi.':'Hareket sürüyor; tekrar deneyin.')}>{labels[m]}</button>)}<button onClick={()=>{paused.current=!paused.current;setPause(paused.current);}} aria-pressed={pause}>{pause?'Devam':'Duraklat'}</button><button onClick={()=>{actors.current=initialActors();setVisualRoles(actors.current.map(a=>({role:a.role,mode:a.mode,cell:a.cell.join(','),moving:false})));setRouting('READY');setNotice('Dekoratif konumlar sıfırlandı.');}}>Karakterleri sıfırla</button></div><p role="status">{notice}{motionReduced?' · Hareket azaltma etkin':''}</p>{floor===1&&<><p data-route-status={routing}>Yerel rota: {routing}</p><ul aria-label="Yerel görsel rol durumları">{visualRoles.map(a=><li key={a.role} data-visual-role={a.role} data-visual-mode={a.mode} data-visual-moving={String(a.moving)}>{a.role} · {a.moving?'Yürüyor':labels[a.mode]} · dekoratif hücre {a.cell}</li>)}</ul></>}
 <aside aria-label="OfficeV0 kaynak incelemesi"><h2>OfficeV0 · Salt okunur kaynak</h2><p>Snapshot: {source.source} · JOIN_HOLD · Gerçek aktif işler: bilinmiyor</p><p>12×10 görsel yerleşim kanonik yerleşim değildir. Kaynak değerleri avatar veya görev bağlamaz.</p><button onClick={()=>void historical.read()} disabled={historical.state.phase==='loading'}>Tarihsel istasyon örneğini oku</button><p role="status">{historical.state.phase==='historical'?'Doğrulanmış biçim · tarihsel örnek (canlı değil)':historical.state.phase==='hold'?'Okuma HOLD':historical.state.phase==='loading'?'Okunuyor…':'Örnek henüz okunmadı'}</p>{historical.data&&<ul>{historical.data.roles.map(r=><li key={r.station_id}>{r.role}: {r.observed}/{r.total} örnek olay</li>)}</ul>}</aside></section>;
}
