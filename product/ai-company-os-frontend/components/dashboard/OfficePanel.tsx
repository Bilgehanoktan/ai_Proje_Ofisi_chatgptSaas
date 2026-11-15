"use client";
import type {ReactNode} from 'react';
import Link from 'next/link';
import {DisplayControls,FloorControls} from '../../design-system/OfficeControls';
import OfficeScene from '../../office/scenes/OfficeScene';
import type {Floor} from '../../office/engine/geometry';
import type fixture from '../../fixtures/office.snapshot.json';
export type SnapshotFloor=typeof fixture.floors[number];
export type Display='scene'|'list'|'engine';
const officeAssets:Record<string,string>={'floor-1':'/office-core.svg','floor-2':'/office-reserve.svg'};
export default function OfficePanel({floors,floorId,onFloor,display,onDisplay,officeOnly,stations,demoFloor,layoutRevision,snapshotRevision,geometryReason}:{floors:readonly SnapshotFloor[];floorId:string;onFloor:(id:string)=>void;display:Display;onDisplay:(d:Display)=>void;officeOnly:boolean;stations:ReactNode;demoFloor:Floor|undefined;layoutRevision:string;snapshotRevision:string;geometryReason:string}){
 const floor=floors.find(f=>f.id===floorId);
 const layoutMatches=snapshotRevision===layoutRevision;
 return <section className="panel office-panel" aria-label="Sanal ofis"><div className="bar"><div><div className="eyebrow">OFFICE-01 / GÖRSEL PROJEKSİYON</div><h2>Sanal ofis</h2><div className="sub">{floor?.name??'Kat bulunamadı'} · STATIC_ONLY</div></div><DisplayControls display={display} onDisplay={onDisplay}>{!officeOnly&&<Link className="action-link" href="/office">Tam ekran ↗</Link>}</DisplayControls></div>
 <FloorControls floors={floors} floorId={floorId} onFloor={onFloor}/>
 {display==='scene'&&(floor&&officeAssets[floor.id]?<div className="scene"><img src={officeAssets[floor.id]} alt={`${floor.name} statik izometrik çizimi`}/><span className="corner">{floor.stations.length?`${floor.stations.length} rezerv istasyon`:'Genişleme rezervi'}</span></div>:<div className="empty" role="status">Bu kat için görsel kaynak yok. Liste kullanılabilir.</div>)}
 {display==='engine'&&(demoFloor?<OfficeScene key={`${layoutRevision}:${demoFloor.id}`} floor={demoFloor}/>:<div className="empty" role="status">Geometri HOLD · {geometryReason}</div>)}
 <div className="station-heading"><h3>İstasyonlar</h3><span className="sub">Klavye ile seçilebilir · gerçek instance yok</span></div>{stations}
 <div className="layout-hold" role="status"><strong>Snapshot ↔ geometri: JOIN_HOLD</strong><span>{layoutMatches?'Sürüm adı eşleşiyor; bağımsız yerleşim kabulü yok.':`Yerleşim revizyonları farklı: ${snapshotRevision} / ${layoutRevision}.`} Geometri yalnız bağımsız demo; canlı hareket ve konum birleştirmesi yok.</span></div></section>;
}
