"use client";
import {useState} from 'react';
import {parseWorkbenchSnapshot,type SampleSnapshot} from './workbenchSnapshot';
import plan from '../../fixtures/core.plan.projection.json';
export default function WorkbenchLifecyclePanel(){
 const [raw,setRaw]=useState(''),[sample,setSample]=useState<SampleSnapshot|null>(null),[status,setStatus]=useState('Örnek okunmadı · HOLD');
 return <section className="panel" aria-label="Sentetik görev yaşam döngüsü"><h2>Görev yaşam döngüsü · D0</h2><p className="sub">0182 CLI snapshot görüntüleyici · kanonik RunState veya gerçek yürütme değil.</p><label htmlFor="workbench-json">Sentetik CLI JSON çıktısı</label><textarea id="workbench-json" rows={4} maxLength={20000} value={raw} onChange={e=>{setRaw(e.target.value);setSample(null);setStatus('Örnek değişti · HOLD');}} style={{display:'block',width:'100%',margin:'8px 0'}}/><div className="bar"><button type="button" onClick={()=>{const x=parseWorkbenchSnapshot(raw);setSample(x);setStatus(x?'Sentetik dosya yapısı eşleşti · DENY':'Uyumsuz örnek · HOLD');}}>Örneği incele</button><button type="button" onClick={()=>{setRaw('');setSample(null);setStatus('Örnek okunmadı · HOLD');}}>Temizle</button></div><p role="status">{status}</p><div className="sectiongrid">{plan.tasks.map(t=><article className="item" key={t.id}><h3>{t.label}</h3><small>{t.role}</small><p>{sample?.tasks.find(s=>s[0]===t.id)?.[1]??'HOLD'}</p></article>)}</div><p>Örnek olay: {sample?.events??'—'} · Dispatch / Release: DENY</p></section>;
}
