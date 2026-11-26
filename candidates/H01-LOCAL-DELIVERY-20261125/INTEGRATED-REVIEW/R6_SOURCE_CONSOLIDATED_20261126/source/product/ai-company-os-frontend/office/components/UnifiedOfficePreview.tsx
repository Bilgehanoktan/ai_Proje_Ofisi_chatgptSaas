'use client';
import {useState} from 'react';
import {createUnifiedOfficePreview} from '../engine/unifiedOfficePreview';
export default function UnifiedOfficePreview(){
 const [preview]=useState(createUnifiedOfficePreview);
 const [selected,setSelected]=useState(preview.initialFloorId);
 const floor=preview.views.find(v=>v.floorId===selected)!;
 return <section className="panel" aria-label="Sentetik çok katlı ofis">
  <div className="eyebrow">U1 / D0 DECORATIVE · JOIN_HOLD</div><h2>Çok katlı ofis önizlemesi</h2>
  <p className="notice">Bu sahne bağımsız sentetik rol şablonlarıdır. Tarihsel görev gözlemi ile ajan, proje veya konum eşleştirmesi yapılmaz.</p>
  <div role="group" aria-label="Kat seçimi" style={{display:'flex',gap:8,flexWrap:'wrap'}}>{preview.views.map((v,i)=><button type="button" key={v.floorId} aria-pressed={v.floorId===selected} onClick={()=>setSelected(v.floorId)}>Kat {i+1} · {v.lifecycle==='DRAFT'?'Taslak':'D0'}</button>)}</div>
  <p role="status">{floor.floorId} · {floor.lifecycle} · {floor.visibleActors} sentetik rol · portal {floor.portalPhase}</p>
  <img src={floor.svgUri} alt={`${floor.floorId}: ${floor.visibleActors} sentetik rol, ${floor.rooms} oda, ${floor.stations} istasyon`} style={{display:'block',width:'100%',height:'auto',maxHeight:'70vh',objectFit:'contain'}}/>
  <p className="sub">Sadece kat görünümü değişir. Görev yürütme, transfer komutu, gerçek ajan yerleştirme veya yetki yok.</p>
 </section>;
}
