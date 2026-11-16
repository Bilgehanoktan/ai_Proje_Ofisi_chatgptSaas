'use client';
import {useEffect,useRef,useState} from 'react';
import {createHybridRender,isoHybrid,hybridBounds,fitHybrid} from '../engine/premiumHybridRender';
import {FRAME,FOOT,frames,atlasSize,avatarFrame} from '../engine/premiumPresentation';
import {paintAtlas} from './premiumAtlasPaint';
import type {Cell} from '../engine/premiumHybridLayout';
const W=1100,H=720,miniBox={x:868,y:12,w:220,h:130};
const names:Record<string,string>={'F1-RSCH':'RESEARCH','F1-ORCH':'ORCHESTRATOR','F1-ENG':'ENGINEERING','F1-QA':'QUALITY','F1-EXP':'PASİF REZERV','F1-BRIEF':'BRIEFING','F1-ENTRY':'GİRİŞ','F1-PORTAL':'KAPALI PORTAL'};
const colors:Record<string,number>={'F1-RSCH':0x325b58,'F1-ORCH':0x385477,'F1-ENG':0x51446b,'F1-QA':0x6a563d,'F1-EXP':0x303946,'F1-BRIEF':0x6a5143,'F1-PORTAL':0x242d38};
const roleColor={orchestrator:0x627fae,research:0x4b9d87,engineer:0x9977cc,qa:0xc68e59};
type CameraAction='in'|'out'|'fit'|'focus'|'left'|'right'|'up'|'down';
export default function PremiumHybridScene(){
 const host=useRef<HTMLDivElement>(null),bridge=useRef<ReturnType<typeof createHybridRender>|null>(null);
 if(!bridge.current)bridge.current=createHybridRender();
 const model=bridge.current;
 const [frame,setFrame]=useState(model.frame),[selected,setSelected]=useState(model.frame().actors[0].id),[status,setStatus]=useState('loading'),[asset,setAsset]=useState('loading'),[paused,setPaused]=useState(false),[reduced,setReduced]=useState(true),[message,setMessage]=useState('Yerel görsel istasyon seçin.');
 const selectedRef=useRef(selected),pauseRef=useRef(false),reduceRef=useRef(true),cameraAction=useRef<(a:CameraAction)=>void>(()=>{});
 useEffect(()=>{const media=window.matchMedia('(prefers-reduced-motion: reduce)');const sync=()=>{reduceRef.current=media.matches;setReduced(media.matches);};sync();media.addEventListener('change',sync);return()=>media.removeEventListener('change',sync);},[]);
 useEffect(()=>{let disposed=false;let game:import('phaser').Game|undefined;let failed=false;
  const fail=()=>{if(disposed||failed)return;failed=true;game?.destroy(true);cameraAction.current=()=>{};setStatus('unavailable');};
  const timeout=window.setTimeout(fail,10000);
  import('phaser').then(({default:P})=>{if(disposed||failed||!host.current)return;
   const l=model.registry.layout,b=hybridBounds(l),point=(x:number,y:number)=>isoHybrid(l,x,y),fit=fitHybrid(l,W,H);
   const scene={create(this:import('phaser').Scene){if(disposed||failed)return;
    const ground=this.add.graphics().setDepth(-100);for(let y=0;y<l.height;y++)for(let x=0;x<l.width;x++){const p=point(x,y),z=l.zones.find(v=>x>=v.rect.x&&x<v.rect.x+v.rect.w&&y>=v.rect.y&&y<v.rect.y+v.rect.h);const c=z&&colors[z.id]||((x+y)%2?0x344557:0x3c4f60);const tile=[{x:p.x,y:p.y-16},{x:p.x+32,y:p.y},{x:p.x,y:p.y+16},{x:p.x-32,y:p.y}];ground.fillStyle(c).fillPoints(tile,true).lineStyle(1,0x98a9b7,.22).strokePoints(tile,true);}
    for(const z of l.zones){const name=names[z.id];if(!name)continue;const p=point(z.rect.x+(z.rect.w-1)/2,z.rect.y);this.add.text(p.x,p.y-30,name,{fontSize:'17px',fontStyle:'bold',color:'#f3eee3',backgroundColor:'#182333',padding:{x:8,y:4}}).setOrigin(.5).setDepth(3e6);}
    // Each physical footprint cell owns its geometry and depth; no new collision authority.
    for(const f of l.footprints)for(let y=f.rect.y;y<f.rect.y+f.rect.h;y++)for(let x=f.rect.x;x<f.rect.x+f.rect.w;x++){const p=point(x,y),g=this.add.graphics().setDepth(p.y*1024+p.x/4096);const X=p.x,Y=p.y;
     if(f.kind==='partition'){g.fillStyle(0x87bbce,.29).fillPoints([{x:X-28,y:Y},{x:X+28,y:Y},{x:X+28,y:Y-42},{x:X-28,y:Y-42}],true).lineStyle(2,0xa4cfda,.8).strokeRect(X-28,Y-42,56,42);}
     else {const warm=f.kind==='table'||f.zoneId==='F1-ORCH';g.fillStyle(0x0d1823,.5).fillEllipse(X,Y+4,49,20).fillStyle(0x283747).fillRect(X-19,Y-26,5,26).fillRect(X+14,Y-26,5,26);g.fillStyle(warm?0xb88e63:0x9cb5bd).fillPoints([{x:X-28,y:Y-26},{x:X,y:Y-39},{x:X+28,y:Y-26},{x:X,y:Y-13}],true);if(f.kind==='desk'){g.fillStyle(0x182838).fillRoundedRect(X-13,Y-61,26,19,3).fillStyle(f.zoneId==='F1-QA'?0xc9ae70:0x75d0ce).fillRoundedRect(X-10,Y-58,20,13,2).fillStyle(0x253747).fillRect(X-2,Y-42,4,10);}else g.fillStyle(0xe3ddcc).fillRect(X-7,Y-29,14,5);}
    }
    for(const s of l.stations){const p=point(...s.anchor);this.add.graphics().setDepth(-90).lineStyle(2,s.activeTemplate?0x93dfd3:0x667684,.7).strokeEllipse(p.x,p.y,36,17);}
    const key='hybrid-shared-d0-atlas';let atlasReady=false;try{const atlas=this.textures.createCanvas(key,atlasSize.w,atlasSize.h);if(atlas){paintAtlas(atlas.getContext());for(const f of frames)if(!atlas.add(f.name,0,f.x,f.y,FRAME,FRAME))throw Error('ATLAS_FRAME');atlas.refresh();atlasReady=true;}}catch{if(this.textures.exists(key))this.textures.remove(key);}
    setAsset(atlasReady?'atlas':'graphics-fallback');const rigs=new Map(model.frame().actors.map(a=>[a.id,{g:this.add.graphics(),sprite:atlasReady?this.add.image(0,0,key,avatarFrame({role:a.role,direction:1,mode:'idle',progress:0},0,false)).setOrigin(.5,FOOT/FRAME).setScale(.65):null}]));
    const cam=this.cameras.main;cam.setBounds(0,0,b.width,b.height);cam.setZoom(fit);cam.centerOn(b.width/2,b.height/2);
    const mini=this.cameras.add(miniBox.x,miniBox.y,miniBox.w,miniBox.h).setName('hybrid-minimap').setZoom(fitHybrid(l,miniBox.w,miniBox.h)).setBackgroundColor('#111c28');mini.centerOn(b.width/2,b.height/2);
    const marker=this.add.graphics().setDepth(4e6);cam.ignore(marker);
    cameraAction.current=a=>{if(a==='fit'){cam.setZoom(fit);cam.centerOn(b.width/2,b.height/2);}else if(a==='focus'){const actor=model.frame().actors.find(v=>v.id===selectedRef.current);if(actor){const p=point(actor.x,actor.y);cam.setZoom(Math.min(1.4,fit*2.5));cam.centerOn(p.x,p.y);}}else if(a==='in'||a==='out')cam.setZoom(P.Math.Clamp(cam.zoom*(a==='in'?1.2:1/1.2),fit,1.6));else {cam.scrollX+=(a==='left'?-1:a==='right'?1:0)*100/cam.zoom;cam.scrollY+=(a==='up'?-1:a==='down'?1:0)*100/cam.zoom;}};
    this.input.on('pointerdown',(p:import('phaser').Input.Pointer)=>{if(p.x>=miniBox.x&&p.x<miniBox.x+miniBox.w&&p.y>=miniBox.y&&p.y<miniBox.y+miniBox.h){const target=mini.getWorldPoint(p.x,p.y);cam.centerOn(target.x,target.y);}});
    let last=-Infinity;this.events.on('update',(time:number,delta:number)=>{if(disposed||failed)return;try{const freeze=pauseRef.current||reduceRef.current,f=model.advance(delta,freeze);for(const a of f.actors){const rig=rigs.get(a.id)!,p=point(a.x,a.y),depth=p.y*1024+p.x/4096+1;rig.g.clear().setDepth(depth-.001);if(a.id===selectedRef.current)rig.g.lineStyle(2,0xe9dcff).strokeEllipse(p.x,p.y+3,29,13);if(rig.sprite){rig.sprite.setPosition(p.x,p.y).setDepth(depth);rig.sprite.setFrame(avatarFrame({role:a.role,direction:a.direction,mode:a.atStation?'work':'idle',progress:a.moving?1:0},time,!freeze));}else rig.g.fillStyle(0x0d1721,.4).fillEllipse(p.x,p.y+3,26,12).fillStyle(roleColor[a.role]).fillRoundedRect(p.x-8,p.y-30,16,26,4).fillStyle(0xe6b99a).fillCircle(p.x,p.y-35,8);}
     const vw=cam.width/cam.zoom,vh=cam.height/cam.zoom;marker.clear().lineStyle(8,0x86e9e0,.9).strokeRect(cam.scrollX+(cam.width-vw)/2,cam.scrollY+(cam.height-vh)/2,vw,vh);if(time-last>=200){last=time;setFrame(f);}
    }catch{fail();}});
    window.clearTimeout(timeout);setStatus('ready');
   }};
   game=new P.Game({type:P.AUTO,width:W,height:H,parent:host.current,backgroundColor:'#131b27',scale:{mode:P.Scale.FIT,autoCenter:P.Scale.CENTER_BOTH},scene});
  }).catch(fail);return()=>{disposed=true;window.clearTimeout(timeout);if(!failed)game?.destroy(true);cameraAction.current=()=>{};};
 },[model]);
 const select=(id:string)=>{selectedRef.current=id;setSelected(id);};
 const command=(target:Cell|null)=>{if(paused||reduced||status!=='ready')return;const ok=target?model.goal(selected,target):model.home(selected);setFrame(model.frame());setMessage(ok?'Dekoratif hedef kabul edildi.':'Hedef dolu/geçersiz veya hareket devam ediyor.');};
 return <section aria-label="Hibrit Premium Ofis"><p role="status">D0 · JOIN_HOLD · 48×30 aday geometri · Gerçek ajan/görev yok · {status}</p><div className="chips">{(['out','fit','in','focus','left','right','up','down'] as const).map(a=><button key={a} disabled={status!=='ready'} onClick={()=>cameraAction.current(a)}>{({out:'−',fit:'Tüm ofis',in:'+',focus:'Odakla',left:'Sol',right:'Sağ',up:'Yukarı',down:'Aşağı'})[a]}</button>)}</div><div ref={host} aria-hidden="true" style={{width:'100%',aspectRatio:'1100 / 720',background:'#131b27'}}/><p>Görsel profil: {asset} · Mini haritaya tıklayarak kamerayı taşı.</p>{status==='unavailable'&&<p role="alert">Yeni sahne kullanılamıyor. <a href="/office/premium/native">Önceki native ofis</a></p>}<div className="chips">{frame.actors.map(a=><button key={a.id} aria-pressed={selected===a.id} onClick={()=>select(a.id)}>{a.role} · {a.id}</button>)}</div><div className="chips"><button disabled={status!=='ready'||paused||reduced||frame.interpolating} onClick={()=>command(model.registry.layout.briefing)}>Briefing alanı</button><button disabled={status!=='ready'||paused||reduced||frame.interpolating} onClick={()=>command(null)}>İstasyona dön</button><button aria-pressed={paused} onClick={()=>{pauseRef.current=!pauseRef.current;setPaused(pauseRef.current);}}>{paused?'Devam':'Duraklat'}</button></div><p role="status">{message} · {frame.status} {frame.reason??''} · {reduced?'Hareket azaltma etkin':''}</p><ul aria-label="Görsel ajanlar">{frame.actors.map(a=><li key={a.id} data-visual-id={a.id}>{a.id} · {a.stationId} · {a.moving?'Yürüyor':a.atStation?'İstasyonda':'Bekliyor'} · görsel konum {a.x.toFixed(1)}, {a.y.toFixed(1)}</li>)}</ul><p>Rezerv istasyonları pasif, portal kapalı. Gerçek Runtime eşleşmesi doğrulanmadı.</p></section>;
}
