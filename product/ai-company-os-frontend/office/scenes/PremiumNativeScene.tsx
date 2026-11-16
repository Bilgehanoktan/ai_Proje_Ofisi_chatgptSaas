'use client';
import {useEffect,useRef,useState} from 'react';
import {advance,command,furniture,initialActors,iso,palette,position,roles,rooms,WIDTH,HEIGHT,type Role,type Mode} from '../engine/premiumModel';

type Status='loading'|'ready'|'unavailable';
const modes:Mode[]=['idle','work','meeting','rest'];
const labels:Record<Mode,string>={idle:'Bekleme',work:'Çalışma',meeting:'Toplantı',rest:'Dinlenme'};
export default function PremiumNativeScene(){
 const host=useRef<HTMLDivElement>(null),actors=useRef(initialActors()),selection=useRef<Role>('orchestrator'),floorRef=useRef(1),paused=useRef(false),reduced=useRef(true);
 const [status,setStatus]=useState<Status>('loading'),[floor,setFloor]=useState(1),[role,setRole]=useState<Role>('orchestrator'),[pause,setPause]=useState(false),[notice,setNotice]=useState('Dekoratif rol seçin.'),[motionReduced,setMotionReduced]=useState(true);
 const [visualRoles,setVisualRoles]=useState(()=>initialActors().map(a=>({role:a.role,mode:a.mode,cell:a.cell.join(','),moving:false})));
 const cameraAction=useRef<(action:'in'|'out'|'reset'|'focus')=>void>(()=>{});
 useEffect(()=>{const mq=window.matchMedia('(prefers-reduced-motion: reduce)');const sync=()=>{reduced.current=mq.matches;setMotionReduced(mq.matches);};sync();mq.addEventListener('change',sync);return()=>mq.removeEventListener('change',sync);},[]);
 useEffect(()=>{let disposed=false;let game:import('phaser').Game|undefined;setStatus('loading');const timeout=window.setTimeout(()=>{if(!disposed){disposed=true;game?.destroy(true);cameraAction.current=()=>{};setStatus('unavailable');}},10000);
 import('phaser').then(({default:P})=>{if(disposed||!host.current)return;
 const scene={create(this:import('phaser').Scene){
  if(disposed)return;
  const active=this.add.container(0,0),reserve=this.add.container(0,0).setVisible(false);
  const tile=(g:import('phaser').GameObjects.Graphics,x:number,y:number,color:number)=>{const p=iso(x,y);const points=[{x:p.x,y:p.y-18},{x:p.x+36,y:p.y},{x:p.x,y:p.y+18},{x:p.x-36,y:p.y}];g.fillStyle(color).fillPoints(points,true).lineStyle(1,0x8798a3,.4).strokePoints(points,true);};
  for(const [layer,empty] of [[active,false],[reserve,true]] as const){const g=this.add.graphics();layer.add(g);for(let x=0;x<WIDTH;x++)for(let y=0;y<HEIGHT;y++){const r=!empty&&rooms.find(r=>x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h);tile(g,x,y,r?r.color:(x+y)%2?0x344554:0x3d4f60);}}
  // Exterior glass accents only; no invisible interior wall is introduced into the path model.
  for(const r of rooms){const a=iso(r.x,r.y),b=iso(r.x+r.w-1,r.y);const glass=this.add.graphics();glass.fillStyle(0x88b3c4,.22).fillPoints([{x:a.x-36,y:a.y},{x:b.x+36,y:b.y},{x:b.x+36,y:b.y-53},{x:a.x-36,y:a.y-53}],true).lineStyle(2,0x7898a8,.9).lineBetween(a.x-36,a.y-53,b.x+36,b.y-53);for(let i=0;i<=r.w;i++){const t=i/r.w,x=a.x-36+(b.x-a.x+72)*t,y=a.y+(b.y-a.y)*t;glass.lineBetween(x,y,x,y-53);}glass.setDepth(a.y-20);active.add(glass);}
  for(const r of rooms){const p=iso(r.x,r.y);const label=this.add.text(p.x,p.y-38,r.name,{fontSize:'13px',color:'#e8e3db',backgroundColor:'#18202c',padding:{x:5,y:3}}).setOrigin(.5);active.add(label);}
  for(const f of furniture){const p=iso(f.x+(f.w-1)/2,f.y+(f.h-1)/2);const g=this.add.graphics();const w=42+18*(f.w-1);g.fillStyle(0x141d25,.6).fillEllipse(p.x,p.y+8,w+12,22);
   if(f.kind==='plant'){g.fillStyle(0xa57e58).fillRect(p.x-8,p.y-13,16,18).fillStyle(0x59876c).fillCircle(p.x,p.y-25,15).fillStyle(0x82ad7b).fillCircle(p.x+7,p.y-34,10);}
   else if(f.kind==='sofa'){g.fillStyle(0x8c9aaf).fillRoundedRect(p.x-w/2,p.y-21,w,25,5).fillStyle(0x56677a).fillRoundedRect(p.x-w/2,p.y-30,w,12,4);}
   else{g.fillStyle(0x5c4537).fillRect(p.x-w/2,p.y-9,w,17).fillStyle(0xc8a779).fillRoundedRect(p.x-w/2,p.y-21,w,17,3);if(f.kind!=='table'){g.fillStyle(0x243644).fillRoundedRect(p.x-13,p.y-40,26,18,3).fillStyle(0x88c6c7).fillRect(p.x-10,p.y-37,20,12).fillStyle(0x313b44).fillRect(p.x-2,p.y-22,4,8);}}
   g.setDepth(p.y);active.add(g);}
  const rigs=roles.map(r=>{const g=this.add.graphics();active.add(g);return {role:r,g};});
  const emptyLabel=this.add.text(550,520,'KAT 2 · PASİF GENİŞLEME REZERVİ',{fontSize:'20px',color:'#b6c7d7'}).setOrigin(.5);reserve.add(emptyLabel);
  const cam=this.cameras.main;cam.setBounds(0,0,1100,720);cam.centerOn(550,360);
  // A second pointer supports pinch. These handlers are local-only and still require real Phaser E2E.
  this.input.addPointer(1);
  const fingers=new Map<number,{x:number;y:number}>();
  const zoomAt=(x:number,y:number,z:number)=>{const old=cam.getWorldPoint(x,y);cam.setZoom(P.Math.Clamp(z,1,2.4));cam.preRender();const next=cam.getWorldPoint(x,y);cam.scrollX+=old.x-next.x;cam.scrollY+=old.y-next.y;};
  const pan=(dx:number,dy:number)=>{cam.scrollX-=dx/cam.zoom;cam.scrollY-=dy/cam.zoom;};
  this.input.on('pointerdown',(p:import('phaser').Input.Pointer)=>{if(p.button===0&&fingers.size<2)fingers.set(p.id,{x:p.x,y:p.y});});
  this.input.on('pointermove',(p:import('phaser').Input.Pointer)=>{const prev=fingers.get(p.id);if(!prev||!p.isDown)return;const next={x:p.x,y:p.y};if(fingers.size===2){const other=[...fingers.entries()].find(([id])=>id!==p.id)?.[1];if(other){const before=Math.hypot(prev.x-other.x,prev.y-other.y),after=Math.hypot(next.x-other.x,next.y-other.y);if(before>4&&after>4){zoomAt((prev.x+other.x)/2,(prev.y+other.y)/2,cam.zoom*after/before);pan((next.x-prev.x)/2,(next.y-prev.y)/2);}}}else pan(next.x-prev.x,next.y-prev.y);fingers.set(p.id,next);});
  const release=(p:import('phaser').Input.Pointer)=>{fingers.delete(p.id);};this.input.on('pointerup',release);this.input.on('pointerupoutside',release);this.input.on('gameout',()=>{fingers.clear();});
  this.input.on('wheel',(p:import('phaser').Input.Pointer,_over:unknown,_dx:number,dy:number)=>{if(!fingers.size)zoomAt(p.x,p.y,cam.zoom*Math.exp(-dy*.0015));});
  cameraAction.current=a=>{if(a==='reset'){cam.setZoom(1);cam.centerOn(550,360);}else if(a==='focus'){const actor=actors.current.find(v=>v.role===selection.current);if(actor&&floorRef.current===1){const p=position(actor);cam.setZoom(1.6);cam.centerOn(p.x,p.y);}}else cam.setZoom(P.Math.Clamp(cam.zoom+(a==='in'?.2:-.2),1,2.4));};
  let lastReadback=-Infinity;
  this.events.on('update',(time:number,delta:number)=>{if(disposed)return;active.setVisible(floorRef.current===1);reserve.setVisible(floorRef.current===2);if(floorRef.current!==1)return;if(!paused.current&&!reduced.current)advance(actors.current,delta/1000);
   for(const rig of rigs){const a=actors.current.find(v=>v.role===rig.role)!;const p=position(a),g=rig.g;const seated=a.progress===0&&['work','meeting','rest'].includes(a.mode),moving=a.progress>0,animated=!paused.current&&!reduced.current;const phase=animated?Math.sin(time/(moving?85:200)):0;const leg=moving?phase*8:0,body=seated?17:25;
    g.clear().fillStyle(0x10151d,.65).fillEllipse(p.x,p.y+3,29,12).lineStyle(5,0x293444).lineBetween(p.x-4,p.y-body+10,p.x-5+leg,p.y).lineBetween(p.x+4,p.y-body+10,p.x+5-leg,p.y).fillStyle(palette[a.role]).fillRoundedRect(p.x-9,p.y-body-15,18,25,5).fillStyle(0xd5ab8a).fillCircle(p.x,p.y-body-22,9).fillStyle(0x3c302b).fillEllipse(p.x,p.y-body-28,18,7).lineStyle(4,0xd5ab8a).lineBetween(p.x-8,p.y-body-7,p.x-13+a.direction*(a.mode==='work'?phase*3:leg*.5),p.y-body+4).lineBetween(p.x+8,p.y-body-7,p.x+12+a.direction*(a.mode==='work'?-phase*3:-leg*.5),p.y-body+4);
    if(a.role===selection.current)g.lineStyle(2,0xd7c6ff).strokeEllipse(p.x,p.y+4,34,15);g.setDepth(p.y+1);
   }active.sort('depth');if(time-lastReadback>=250){lastReadback=time;setVisualRoles(actors.current.map(a=>({role:a.role,mode:a.mode,cell:a.cell.join(','),moving:a.progress>0})));}});
  window.clearTimeout(timeout);if(!disposed)setStatus('ready');
 }};
 game=new P.Game({type:P.AUTO,width:1100,height:720,parent:host.current,backgroundColor:'#131b27',scale:{mode:P.Scale.FIT,autoCenter:P.Scale.CENTER_BOTH},scene});
 }).catch(()=>{window.clearTimeout(timeout);if(!disposed){disposed=true;game?.destroy(true);setStatus('unavailable');}});
 return()=>{window.clearTimeout(timeout);if(!disposed){disposed=true;game?.destroy(true);}cameraAction.current=()=>{};};},[]);
 function select(r:Role){selection.current=r;setRole(r);cameraAction.current('focus');}
 function changeFloor(n:number){floorRef.current=n;setFloor(n);cameraAction.current('reset');}
 return <section aria-label="Native premium ofis"><p className="notice" role="status">D0 · JOIN_HOLD · Dekoratif rol şablonları, gerçek ajan veya görev yok. {status}</p><div className="chips"><button aria-pressed={floor===1} onClick={()=>changeFloor(1)}>Kat 1</button><button aria-pressed={floor===2} onClick={()=>changeFloor(2)}>Kat 2 · Rezerv</button>{(['out','reset','in','focus'] as const).map(a=><button key={a} disabled={status!=='ready'||(a==='focus'&&floor!==1)} onClick={()=>cameraAction.current(a)}>{({out:'−',reset:'Sıfırla',in:'+',focus:'Ajanı odakla'})[a]}</button>)}</div><div ref={host} style={{width:'100%',aspectRatio:'1100 / 720',touchAction:'none',background:'#131b27'}} aria-hidden="true"/>{status!=='ready'&&<p role="status">{status==='loading'?'Motor yükleniyor…':'Phaser kullanılamıyor. '}<a href="/office/premium">Gömülü ofis önizlemesi ↗</a></p>}<div className="chips">{roles.map(r=><button key={r} disabled={floor!==1} aria-pressed={role===r} onClick={()=>select(r)}>{r}</button>)}</div><div className="chips">{modes.map(m=><button key={m} disabled={status!=='ready'||floor!==1||motionReduced} onClick={()=>setNotice(command(actors.current,role,m)?'Dekoratif komut kabul edildi.':'Hareket sürüyor; tekrar deneyin.')}>{labels[m]}</button>)}<button onClick={()=>{paused.current=!paused.current;setPause(paused.current);}} aria-pressed={pause}>{pause?'Devam':'Duraklat'}</button><button onClick={()=>{actors.current=initialActors();setNotice('Dekoratif konumlar sıfırlandı.');}}>Karakterleri sıfırla</button></div><p role="status">{notice}{motionReduced?' · Hareket azaltma etkin':''}</p>{floor===1&&<ul aria-label="Yerel görsel rol durumları">{visualRoles.map(a=><li key={a.role} data-visual-role={a.role} data-visual-mode={a.mode} data-visual-moving={String(a.moving)}>{a.role} · {a.moving?'Yürüyor':labels[a.mode]} · dekoratif hücre {a.cell}</li>)}</ul>}</section>;
}
