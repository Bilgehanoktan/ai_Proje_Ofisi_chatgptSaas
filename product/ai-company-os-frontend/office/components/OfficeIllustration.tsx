"use client";
import {useRef,useState} from 'react';
import type {PointerEvent} from 'react';
import {officeArtwork,officeImageUri} from '../engine/officeArtwork';
import {HOME,MIN_ZOOM,MAX_ZOOM,zoomCamera,panCamera,dragCamera,focusCamera,imagePlacement,type GalleryCamera} from '../engine/galleryCamera';
import {iso,type Floor} from '../engine/geometry';
import {rolePortraitUri,roomVisual} from '../../design-system/roleVisuals';
import styles from './OfficeIllustration.module.css';
export default function OfficeIllustration({floor}:{floor:Floor}){
 const [selected,setSelected]=useState<string|null>(null),[camera,setCamera]=useState<GalleryCamera>({...HOME}),[dragging,setDragging]=useState(false);
 const drag=useRef<{id:number;x:number;y:number}|null>(null);
 const art=officeArtwork(floor,selected);
 if(!art.ok)return <div className="empty" role="status">Görsel HOLD · {art.reason}</div>;
 const station=art.stations.find(s=>s.id===selected),placement=imagePlacement(camera);
 function endDrag(e:PointerEvent<HTMLDivElement>){if(drag.current?.id!==e.pointerId)return;drag.current=null;setDragging(false);if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}
 function startDrag(e:PointerEvent<HTMLDivElement>){if(camera.zoom<=1||e.button!==0||e.pointerType==='touch'||drag.current)return;e.currentTarget.setPointerCapture(e.pointerId);drag.current={id:e.pointerId,x:e.clientX,y:e.clientY};setDragging(true);}
 function moveDrag(e:PointerEvent<HTMLDivElement>){const d=drag.current;if(!d||d.id!==e.pointerId)return;const rect=e.currentTarget.getBoundingClientRect(),dx=e.clientX-d.x,dy=e.clientY-d.y;drag.current={id:d.id,x:e.clientX,y:e.clientY};setCamera(c=>dragCamera(c,dx,dy,rect.width,rect.height));}
 function changeZoom(step:number){setCamera(c=>zoomCamera(c,c.zoom+step));}
 return <div className={styles.studio}>
  <div className="bar"><strong>İzometrik ofis galerisi</strong><span className="pill">D0 · REZERV</span></div>
  <div className={styles.floorFacts} aria-label="Geometri katalog özeti"><span>{floor.rooms.length} demo oda</span><span>{art.stations.length} rezerv istasyon</span><span>Gerçek ajan yok</span></div>
  <div className={styles.camera} role="group" aria-label="Galeri kamera kontrolü">
   <button type="button" disabled={camera.zoom<=MIN_ZOOM} onClick={()=>changeZoom(-.25)} aria-label="Uzaklaştır">−</button>
   <button type="button" onClick={()=>setCamera({...HOME})} aria-label="Kamerayı sıfırla">{Math.round(camera.zoom*100)}% · Sıfırla</button>
   <button type="button" disabled={camera.zoom>=MAX_ZOOM} onClick={()=>changeZoom(.25)} aria-label="Yakınlaştır">+</button>
   {([[-60,0,'Sol'],[60,0,'Sağ'],[0,-40,'Yukarı'],[0,40,'Aşağı']] as const).map(([x,y,name])=><button type="button" key={name} disabled={camera.zoom<=1} onClick={()=>setCamera(c=>panCamera(c,x,y))}>{name}</button>)}
  </div>
  <div className={styles.stage} data-draggable={camera.zoom>1?'true':'false'} data-dragging={dragging?'true':'false'} role="region" aria-label="Görsel ofis kamerası" tabIndex={0}
   onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={endDrag} onLostPointerCapture={endDrag}
   onKeyDown={e=>{const moves:Record<string,[number,number]>={ArrowLeft:[-60,0],ArrowRight:[60,0],ArrowUp:[0,-40],ArrowDown:[0,40]};const m=Object.hasOwn(moves,e.key)?moves[e.key]:undefined;if(m&&camera.zoom>1){e.preventDefault();setCamera(c=>panCamera(c,...m));}}}>
   <img src={officeImageUri(art.svg)} alt="Dekoratif izometrik ofis; bütün istasyonlar rezerv, gerçek ajan yok" width={900} height={510} draggable={false} style={{width:placement.width+'%',left:placement.left+'%',top:placement.top+'%'}}/>
  </div>
  <p className={styles.hint}>Yakınlaştır, ok düğmeleriyle kaydır veya sahneyi fareyle sürükle. Mobilde düğmeleri kullan.</p>
  {floor.rooms.length>0&&<section className={styles.directory} aria-label="Demo departmanları"><h3>Departmanlar</h3><div className={styles.roomGrid}>{floor.rooms.map(r=>{const v=roomVisual(r.id),count=art.stations.filter(s=>s.room===r.id).length;return <button type="button" className={styles.roomCard} key={r.id} aria-label={r.label+' odasına odaklan'} onClick={()=>{const p=iso(r.x+(r.w-1)/2,r.y+(r.h-1)/2);setSelected(null);setCamera(focusCamera(p.x,p.y+26));}}><span className={styles.roomMark} style={{background:v?.accent??'#a9b5c5'}} aria-hidden="true"/><span><strong>{r.label}</strong><small>{v?.motif??'Demo oda'} · {count} rezerv</small></span><span aria-hidden="true">↗</span></button>;})}</div></section>}
  <div className={styles.stations} role="group" aria-label="Geometri istasyon seçimi">{art.stations.map(s=><button type="button" key={s.id} aria-pressed={selected===s.id} onClick={()=>{setSelected(s.id);setCamera(focusCamera(s.x,s.y));}}><img src={rolePortraitUri(s.role)} width={32} height={32} alt=""/><span>{s.role} · REZERV</span></button>)}</div>
  <div className={styles.context} aria-live="polite">{station?<><strong>{station.role} · geometri şablonu</strong><span>Oda: {floor.rooms.find(r=>r.id===station.room)?.label??'—'} · Instance yok</span><button type="button" onClick={()=>setCamera(focusCamera(station.x,station.y))}>İstasyona odaklan</button><button type="button" onClick={()=>setSelected(null)}>Seçimi temizle</button></>:<span>{art.stations.length?'Vurgu için istasyon seçin.':'Genişleme rezervi · istasyon yok.'}</span>}</div>
  <p className="sub">Kamera ve mobilyalar yalnız görsel. Snapshot ile JOIN_HOLD; gerçek yerleşim, ajan veya hareket yok.</p>
 </div>;
}
