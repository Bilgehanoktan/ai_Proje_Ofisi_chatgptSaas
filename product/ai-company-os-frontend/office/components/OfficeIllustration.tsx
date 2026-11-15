"use client";
import {useState} from 'react';
import {officeArtwork,officeImageUri} from '../engine/officeArtwork';
import type {Floor} from '../engine/geometry';
import styles from './OfficeIllustration.module.css';
export default function OfficeIllustration({floor}:{floor:Floor}){
 const [selected,setSelected]=useState<string|null>(null);
 const art=officeArtwork(floor,selected);
 if(!art.ok)return <div className="empty" role="status">Görsel HOLD · {art.reason}</div>;
 const station=art.stations.find(s=>s.id===selected);
 return <div className={styles.studio}>
  <div className="bar"><strong>İzometrik ofis galerisi</strong><span className="pill">D0 · REZERV</span></div>
  <div className={styles.stage}><img src={officeImageUri(art.svg)} alt="Dekoratif izometrik ofis; bütün istasyonlar rezerv, gerçek ajan yok" width={900} height={510}/></div>
  <div className={styles.stations} role="group" aria-label="Geometri istasyon seçimi">{art.stations.map(s=><button type="button" key={s.id} aria-pressed={selected===s.id} onClick={()=>setSelected(s.id)}>{s.role} · REZERV</button>)}</div>
  <div className={styles.context} aria-live="polite">{station?<><strong>{station.role} · geometri şablonu</strong><span>Oda: {floor.rooms.find(r=>r.id===station.room)?.label??'—'} · Instance yok</span><button type="button" onClick={()=>setSelected(null)}>Seçimi temizle</button></>:<span>{art.stations.length?'Vurgu için istasyon seçin.':'Genişleme rezervi · istasyon yok.'}</span>}</div>
  <p className="sub">Mobilyalar, kısmi duvarlar ve rol simgeleri yalnız dekoratif. Snapshot ile JOIN_HOLD; gerçek yerleşim, ajan veya hareket yok.</p>
 </div>;
}
