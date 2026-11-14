"use client";
import {useEffect,useMemo,useRef,useState} from 'react';
import {cameraView,iso,markerPosition,pointKey,route,type Floor,type Point} from './geometry';

type View = {zoom:number;x:number;y:number};
type Visual = {view:View;path:Point[]|null;playing:boolean;selected:string|null;playId:number};
const home:View={zoom:1,x:0,y:0};
const assets:Record<string,string>={'floor-1':'/office-core.svg','floor-2':'/office-reserve.svg'};

// This scene consumes only a validated demo layout. Its station selection is local to the preview.
// Parent keys by floor/revision; camera, marker and station changes do not recreate Phaser.
export default function OfficeScene({floor}:{floor:Floor}){
 const host=useRef<HTMLDivElement>(null);
 const [status,setStatus]=useState<'loading'|'ready'|'unavailable'>('loading');
 const [view,setView]=useState<View>(home),[selected,setSelected]=useState<string|null>(null);
 const [start,setStart]=useState('2,0'),[end,setEnd]=useState('2,5'),[showPath,setShowPath]=useState(false);
 const [playing,setPlaying]=useState(false),[playId,setPlayId]=useState(0),[reduced,setReduced]=useState(true);
 const points=useMemo(()=>floor.walkable.map(p=>[p[0],p[1]] as Point),[floor]);
 const path=useMemo(()=>{
  const a=points.find(p=>pointKey(p)===start),b=points.find(p=>pointKey(p)===end);
  return floor.stations.length&&a&&b?route(floor,a,b):null;
 },[floor,points,start,end]);
 const visiblePath=showPath?path:null;
 const visual=useRef<Visual>({view,path:null,playing:false,selected:null,playId:0});
 useEffect(()=>{visual.current={view,path:visiblePath,playing:playing&&!reduced&&status==='ready',selected,playId};},[view,visiblePath,playing,reduced,status,selected,playId]);
 useEffect(()=>{
  const mq=window.matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>{setReduced(mq.matches);if(mq.matches)setPlaying(false);};
  update();mq.addEventListener('change',update);return()=>mq.removeEventListener('change',update);
 },[]);
 useEffect(()=>{
  let cancelled=false;let game:import('phaser').Game|undefined;
  setStatus('loading');
  // A failed or stalled engine must not conceal the original static reference.
  const bootTimer=window.setTimeout(()=>{if(!cancelled){cancelled=true;game?.destroy(true);setStatus('unavailable');}},10000);
  import('phaser').then(({default:P})=>{
   if(cancelled||!host.current)return;
   let pathGraphics:import('phaser').GameObjects.Graphics|undefined;
   let highlight:import('phaser').GameObjects.Graphics|undefined;
   let marker:import('phaser').GameObjects.Arc|undefined;
   let lastPath:Point[]|null|undefined,lastSelected:string|null|undefined,lastView:View|undefined;
   let elapsed=0,lastPlayId=-1;
   const scene={
    create(this:import('phaser').Scene){
     if(cancelled)return;
     const g=this.add.graphics();
     const diamond=(x:number,y:number,color:number)=>{const a=iso(x,y);const ps=[{x:a.x,y:a.y},{x:a.x+51,y:a.y+26},{x:a.x,y:a.y+52},{x:a.x-51,y:a.y+26}];g.fillStyle(color);g.lineStyle(1,0x547080);g.fillPoints(ps,true);g.strokePoints(ps,true);};
     for(let x=0;x<6;x++)for(let y=0;y<6;y++){
      const r=floor.rooms.find(r=>x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h);diamond(x,y,r?Number('0x'+r.color.slice(1)):(x+y)%2?0x263b4e:0x344b5d);
     }
     for(const r of floor.rooms){const a=iso(r.x+(r.w-1)/2,r.y+(r.h-1)/2);this.add.text(a.x,a.y+42,r.label,{fontSize:'13px',color:'#ffffff',backgroundColor:'#101b29'}).setOrigin(.5);}
     for(const s of [...floor.stations].sort((a,b)=>a.x+a.y-b.x-b.y)){
      const a=iso(s.x,s.y),cx=a.x,cy=a.y+26;
      this.add.rectangle(cx,cy-6,66,33,0x9b7850).setStrokeStyle(2,0xd6bf99);
      this.add.rectangle(cx,cy-19,29,16,0x142435).setStrokeStyle(1,0x7aa9bb);
      this.add.rectangle(cx,cy+16,16,13,0x60778e).setStrokeStyle(1,0x93a9ba);
      this.add.text(cx,cy-38,s.role.toUpperCase(),{fontSize:'11px',color:'#e1e9f0',backgroundColor:'#101b29'}).setOrigin(.5);
      this.add.zone(cx,cy,76,55).setInteractive({useHandCursor:true}).on('pointerdown',()=>{if(!cancelled)setSelected(s.id);});
     }
     if(!floor.stations.length)this.add.text(450,440,'GENİŞLEME REZERVİ',{fontSize:'17px',color:'#d1dde8'}).setOrigin(.5);
     pathGraphics=this.add.graphics().setDepth(5);highlight=this.add.graphics().setDepth(6);
     marker=this.add.circle(0,0,7,0xf4d48a).setStrokeStyle(2,0x101b29).setDepth(7).setVisible(false);
     window.clearTimeout(bootTimer);if(!cancelled)setStatus('ready');
    },
    update(this:import('phaser').Scene,_time:number,delta:number){
     if(cancelled||!pathGraphics||!highlight||!marker)return;
     const v=visual.current;
     if(lastView!==v.view){const c=cameraView(v.view.zoom,v.view.x,v.view.y);this.cameras.main.setZoom(c.zoom);this.cameras.main.centerOn(c.x,c.y);lastView=v.view;}
     if(lastSelected!==v.selected){highlight.clear();const s=floor.stations.find(s=>s.id===v.selected);if(s){const a=iso(s.x,s.y);highlight.lineStyle(3,0xf4d48a);highlight.strokeEllipse(a.x,a.y+26,86,56);}lastSelected=v.selected;}
     if(lastPath!==v.path){pathGraphics.clear();elapsed=0;lastPath=v.path;if(v.path){const ps=v.path.map(([x,y])=>{const a=iso(x,y);return {x:a.x,y:a.y+26};});pathGraphics.lineStyle(4,0x78dfce);if(ps.length>1)pathGraphics.strokePoints(ps,false);pathGraphics.fillStyle(0x78dfce);for(const p of ps)pathGraphics.fillCircle(p.x,p.y,4);}}
     if(lastPlayId!==v.playId){elapsed=0;lastPlayId=v.playId;}
     if(!v.path||!v.playing){marker.setVisible(false);return;}
     // One-shot, visual-only traversal; no event publishing and no agent object.
     elapsed+=Math.max(0,Math.min(100,delta));const distance=Math.min(v.path.length-1,elapsed/450);const p=markerPosition(v.path,distance);
     if(p)marker.setPosition(p.x,p.y).setVisible(true);
     if(distance>=v.path.length-1){visual.current={...v,playing:false};setPlaying(false);}
    }
   };
   game=new P.Game({type:P.AUTO,width:900,height:510,parent:host.current,backgroundColor:'#101b29',scale:{mode:P.Scale.FIT,autoCenter:P.Scale.CENTER_BOTH},scene});
  }).catch(()=>{window.clearTimeout(bootTimer);if(!cancelled){cancelled=true;game?.destroy(true);setStatus('unavailable');}});
  return()=>{window.clearTimeout(bootTimer);if(!cancelled){cancelled=true;game?.destroy(true);}};
 },[floor]);
 function resetRoute(){setPlaying(false);setShowPath(false);}
 function move(dx:number,dy:number){setView(v=>{const c=cameraView(v.zoom,v.x+dx,v.y+dy);return {zoom:c.zoom,x:c.x-450,y:c.y-255};});}
 function zoomBy(d:number){setView(v=>{const c=cameraView(v.zoom,v.x,v.y);const n=cameraView(c.zoom+d,c.x-450,c.y-255);return {zoom:n.zoom,x:n.x-450,y:n.y-255};});}
 return <div className="office-engine-preview">
  <div className="bar"><strong>Geometri stüdyosu · {floor.name}</strong><span className="pill">DEMO / {status==='ready'?'SAHNE HAZIR':status==='loading'?'YÜKLENİYOR':'FALLBACK'}</span></div>
  <div className="chips camera-controls" aria-label="Görsel kamera"><button disabled={status!=='ready'} onClick={()=>zoomBy(-.15)}>−</button><button disabled={status!=='ready'} onClick={()=>setView(home)}>Kamera {Math.round(view.zoom*100)}% · Sıfırla</button><button disabled={status!=='ready'} onClick={()=>zoomBy(.15)}>+</button>{([[-50,0,'Sol'],[50,0,'Sağ'],[0,-35,'Yukarı'],[0,35,'Aşağı']] as const).map(([x,y,label])=><button key={label} disabled={status!=='ready'||view.zoom<=1} onClick={()=>move(x,y)}>{label}</button>)}</div>
  <div className="engine-frame"><div ref={host} className="sceneEngine" aria-hidden="true"/>{status!=='ready'&&<div className="engine-fallback"><img src={assets[floor.id]} alt={`${floor.name} statik ofis referansı`}/><span role="status">{status==='loading'?'Görsel motor yükleniyor…':'Görsel motor kullanılamıyor. Statik referans ve liste kullanılabilir.'}</span></div>}</div>
  <div className="engine-stations" aria-label="Yalnız geometri istasyonları">{floor.stations.map(s=><button key={s.id} aria-pressed={selected===s.id} onClick={()=>setSelected(s.id)}>{s.role} · ({s.x},{s.y}) · REZERV</button>)}</div>
  {floor.stations.length>0?<div className="route-controls"><h3>Sentetik koridor rotası</h3><div className="chips"><label>Başlangıç <select value={start} onChange={e=>{setStart(e.target.value);resetRoute();}}>{points.map(p=><option key={pointKey(p)} value={pointKey(p)}>{pointKey(p)}</option>)}</select></label><label>Bitiş <select value={end} onChange={e=>{setEnd(e.target.value);resetRoute();}}>{points.map(p=><option key={pointKey(p)} value={pointKey(p)}>{pointKey(p)}</option>)}</select></label><button disabled={!path} aria-pressed={showPath} onClick={()=>{setShowPath(v=>!v);setPlaying(false);}}>Rotayı {showPath?'gizle':'göster'}</button><button disabled={!showPath||!path||path.length<2||reduced||status!=='ready'||playing} onClick={()=>{setPlayId(v=>v+1);setPlaying(true);}}>İşaretçiyi oynat</button><button disabled={!playing} onClick={()=>setPlaying(false)}>Durdur</button></div><p className="sub" role="status">{!path?'Rota yok · HOLD':`${path.length-1} adım · görsel BFS`}{reduced?' · Hareket azaltma etkin':''}. İşaretçi ajan değildir.</p></div>:<p className="sub">Genişleme rezervi: hareket ve istasyon yok.</p>}
  <p className="sub">Bağımsız demo geometrisi; snapshot ile koordinat birleştirme, gerçek placement, agent instance, kapı/kat geçiş grafı veya olay akışı yok.</p>
 </div>;
}
