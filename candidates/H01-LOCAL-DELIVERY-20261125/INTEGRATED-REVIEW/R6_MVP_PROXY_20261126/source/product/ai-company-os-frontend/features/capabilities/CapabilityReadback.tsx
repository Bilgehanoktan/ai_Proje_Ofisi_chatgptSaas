"use client";
import {useState} from 'react';
import ExternalSkillCatalog from './ext06/ExternalSkillCatalog';
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import {skillBoundary} from '../evidence/studioGovernance';
import {areas,roles,filterEntries,selectedEntry,studioBoundary,type Area,type Role} from './studioCatalog';
const areaLabels:Record<Area,string>={all:'Tümü',skill:'Beceri',memory:'Hafıza',knowledge:'Bilgi kaynağı'};
const roleLabels:Record<Role,string>={all:'Tüm roller',orchestrator:'Orchestrator',research:'Research',engineer:'Engineer',qa:'QA'};
export default function CapabilityReadback(){
 const {state,data,read,reset}=useProjectionRead('mvp');
 const skill=skillBoundary(), boundary=studioBoundary();
 const [area,setArea]=useState<Area>('all'),[role,setRole]=useState<Role>('all'),[query,setQuery]=useState(''),[id,setId]=useState('');
 const [skillReset,setSkillReset]=useState(0);
 const visible=filterEntries(area,role,query), selected=selectedEntry(visible,id);
 function clear(){setArea('all');setRole('all');setQuery('');setId('');setSkillReset(v=>v+1);reset();}
 return <section className="panel projection-summary" aria-label="Model, beceri ve hafıza incelemesi"><div className="bar"><div><div className="eyebrow">CAPABILITY / D0 · P10J21</div><h2>Model, Skill ve Memory Studio</h2><small>Salt okunur tanılama · sağlayıcı veya tool çağrısı yok</small></div><div className="chips"><button type="button" onClick={read} disabled={state.phase==='loading'}>Tanılamayı oku</button><button type="button" onClick={clear}>Temizle</button></div></div>
 <p role="status" className="projection-read-status" data-phase={state.phase}>{readStatus(state,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Sentetik tanılama · DENY',hold:'Tanılama doğrulanamadı · HOLD'})}</p>
 <h3>Kaynak adayları · şirket bilgi ve yetkinlik merkezi</h3><p className="sub">Sabit P10J20 kaynak envanteri. Gerçek beceri kaydı, hafıza içeriği veya ajan ataması değildir. Rol filtreleri önerilen inceleme bağlamıdır.</p>
 <div className="chips" role="group" aria-label="Kaynak alanı">{areas.map(a=><button key={a} type="button" aria-pressed={area===a} onClick={()=>{setArea(a);setId('');}}>{areaLabels[a]}</button>)}</div>
 <div className="chips" role="group" aria-label="İnceleme rolü">{roles.map(r=><button key={r} type="button" aria-pressed={role===r} onClick={()=>{setRole(r);setId('');}}>{roleLabels[r]}</button>)}</div>
 <label>Kaynak adaylarında ara <input value={query} maxLength={200} onChange={e=>{setQuery(e.target.value);setId('');}} placeholder="Manifest, ACL, tombstone…"/></label>
 <p aria-live="polite" className="sub">{visible.length} kaynak adayı · Kurulu beceri / gerçek hafıza: {boundary.installedCount===null?'bilinmiyor':'—'}</p>
 <div className="sectiongrid">{visible.map(e=><article className="item" key={e.id}><h3>{e.title}</h3><p>{e.review}</p><small>{areaLabels[e.area]} · {e.boundary}</small><div className="chips"><button type="button" aria-pressed={selected?.id===e.id} onClick={()=>setId(e.id)}>Kaynağı incele</button></div></article>)}</div>
 {!visible.length&&<p className="empty">Bu filtrede kaynak adayı yok.</p>}
 {selected&&<section className="item" aria-label="Kaynak denetçisi"><div className="bar"><h3>{selected.title}</h3><button type="button" onClick={()=>setId('')}>Kapat</button></div><p style={{overflowWrap:'anywhere'}}>{selected.path}</p><p style={{overflowWrap:'anywhere'}}>Git blob: <code>{selected.blob}</code></p><p>Simge: <code>{selected.symbol}</code></p><p>İnceleme bağlamı: {selected.contexts.map(r=>roleLabels[r]).join(', ')} · atama değil</p><p>{selected.review}</p><small>{selected.boundary} · veri içeriği, yükleme, retrieval ve release kapalı.</small></section>}
 <ExternalSkillCatalog key={skillReset}/>
 <h3>Skill Studio · yetkinlik yaşam döngüsü</h3><div className="sectiongrid">{skill.stages.map(s=><article className="item" key={s.id}><h3>{s.label}</h3><small>{s.status} · tasarım kapısı</small></article>)}</div><p className="sub">Kurulu / etkin beceri sayısı: bilinmiyor · etkin araç listesi: yok (D0 sınırı). Yükleme, grant ve çalıştırma kapalı; gerçek beceri kataloğu okunmadı.</p>
 <div className="sectiongrid">{(['model','gateway','tools'] as const).map(k=><article className="item" key={k}><h3>{k}</h3><p>{data?.sections[k]??'—'}</p><small>Tanılama · gerçek etkinlik değil</small></article>)}<article className="item"><h3>Kurumsal hafıza</h3><p>0196-MA kaynak adayı · UI API yok</p><small>ACL / witness / release HOLD · içerik veya retrieval sonucu gösterilmez</small></article></div><p className="sub">Model rezervasyon binding, aktif lease ve bağımsız ACL ayrıca doğrulanmalıdır. Kapanmış 0196-L örneği model veya retrieval için kullanılamaz. Bu ekran hiçbir işlem başlatmaz.</p></section>;
}
