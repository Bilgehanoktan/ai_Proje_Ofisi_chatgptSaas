"use client";
import {useId,useState} from 'react';
import {filterSources,selectSource,type Domain} from './controlSourceCatalog';
export default function ControlSourceInspector({domain}:{domain:Domain}){
 const [query,setQuery]=useState(''),[id,setId]=useState('');
 const searchId=useId(),visible=filterSources(domain,query),selected=selectSource(domain,query,id);
 return <section aria-label="Kaynak denetçisi"><div className="bar"><div><h3>Kaynak ve kanıt denetçisi</h3><p className="sub">Sabit P10J21 kaynak envanteri · canlı işlem, makbuz veya finansal kayıt değildir.</p></div><button type="button" onClick={()=>{setQuery('');setId('');}}>Filtreyi temizle</button></div>
 <label htmlFor={searchId}>Kaynak veya kontrol ara</label><input id={searchId} type="search" value={query} maxLength={200} onChange={e=>{setQuery(e.target.value);setId('');}} placeholder="Kaynak, fonksiyon, kontrol…" style={{width:'100%',minWidth:0,minHeight:44,font:'inherit'}}/>
 <p role="status" className="sub">{visible.length} kaynak adayı · salt okunur</p><div className="sectiongrid">{visible.map(s=><article className="item" key={s.id}><h3>{s.title}</h3><p>{s.limit}</p><small>{s.boundary} · tasarım sınırı</small><div className="chips"><button type="button" aria-pressed={selected?.id===s.id} onClick={()=>setId(s.id)}>Kaynağı incele</button></div></article>)}</div>
 {!visible.length&&<p className="empty">Eşleşen kaynak adayı yok.</p>}
 {selected&&<section className="item" aria-label="Seçili kaynak" style={{overflowWrap:'anywhere'}}><div className="bar"><h3>{selected.title}</h3><button type="button" onClick={()=>setId('')}>Kapat</button></div><p>{selected.path}</p><p>Git blob: <code>{selected.blob}</code></p><p>Fonksiyon: <code>{selected.symbol}</code></p><h4>Gerekli kontrol girdileri</h4><p>{selected.requires}</p><h4>Yetki sınırı</h4><p>{selected.limit}</p><small>{selected.boundary} · bağımsız kabul veya canlı durum değil</small></section>}</section>;
}
