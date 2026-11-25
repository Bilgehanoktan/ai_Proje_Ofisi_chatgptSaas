"use client";
import {useId,useState} from 'react';
import {readSkillCatalog,filterSkills,selectedSkill,emptyFilter,skillBoundary,type Filter} from './skillStudioModel';
import styles from './ExternalSkillCatalog.module.css';
export default function ExternalSkillCatalog(){
 const [filters,setFilters]=useState<Filter>(emptyFilter),[id,setId]=useState('');
 const baseId=useId(); const result=readSkillCatalog(); const boundary=skillBoundary();
 function change<K extends keyof Filter>(key:K,value:Filter[K]){setFilters(f=>({...f,[key]:value}));setId('');}
 if(!result.ok)return <section className="item" role="alert">EXT-06 katalog · HOLD · {result.reason}</section>;
 const c=result.catalog,visible=filterSkills(c,filters),selected=selectedSkill(visible,id);
 return <section className={styles.catalog} aria-labelledby={baseId+'-title'}>
  <div className="bar"><div><div className="eyebrow">SKILL STUDIO / EXT-06</div><h3 id={baseId+'-title'}>Harici yetenek kaynak kataloğu</h3><small>Tarihsel sentetik EXT-05 · salt okunur · gerçek kayıt değil</small></div><span className="pill">QUARANTINED · DENY</span></div>
  <div className={styles.metrics}>{[['Kaynak adayı',c.skills.length],['Kurulu aday',c.installed_count],['Etkin aday',c.active_count],['Etkin araç',0]].map(([label,n])=><article className="item" key={label}><small>{label}</small><strong>{n}</strong></article>)}</div>
  <p className="sub">Gerçek kurulu / etkin beceri ve ajan ataması: {boundary.actualInstalled===null?'bilinmiyor':'—'}. Rol ve departman filtreleri önerilen bağlamdır; gerçek kişi veya grant değildir.</p>
  <div className={styles.filters}>
   <label htmlFor={baseId+'-role'}>Ajan rol şablonu<select id={baseId+'-role'} value={filters.role} onChange={e=>change('role',e.target.value)}><option value="all">Tüm roller</option>{Object.entries(c.roles).map(([k,r])=><option key={k} value={k}>{r.label}</option>)}</select></label>
   <label htmlFor={baseId+'-department'}>Departman<select id={baseId+'-department'} value={filters.department} onChange={e=>change('department',e.target.value)}><option value="all">Tüm departmanlar</option>{Object.values(c.roles).map(r=><option key={r.department} value={r.department}>{r.department}</option>)}</select></label>
   <label htmlFor={baseId+'-search'}>Yetenek ara<input id={baseId+'-search'} type="search" maxLength={200} value={filters.query} onChange={e=>change('query',e.target.value)} placeholder="Skill, sürüm, kaynak…"/></label>
   <button type="button" onClick={()=>{setFilters(emptyFilter());setId('');}}>Filtreleri temizle</button>
  </div>
  <p role="status" className="sub">{visible.length}/{c.skills.length} kaynak adayı gösteriliyor</p>
  <div className={styles.cards}>{visible.map(s=><article key={s.skill_id} className="item"><h4>{s.name}</h4><p>{s.description}</p><small>{s.version} · {s.role_hints.map(r=>c.roles[r as keyof typeof c.roles].label).join(' / ')}</small><p className={styles.hold}>QUARANTINED · Etkin değil</p><button type="button" aria-pressed={id===s.skill_id} onClick={()=>setId(s.skill_id)}>Kaynak ve kanıtı incele</button></article>)}</div>
  {!visible.length&&<p className="empty">Bu rol/departman ve arama için kaynak adayı yok.</p>}
  {selected&&<section className="item" aria-label="Harici yetenek kaynak denetçisi"><div className="bar"><h4>{selected.name} · kaynak denetçisi</h4><button type="button" onClick={()=>setId('')}>Kapat</button></div><dl className={styles.details}>
   {[
    ['Sürüm',selected.version],['Kaynak yolu',selected.source_path],['Kaynak commit',selected.source_commit],['Upstream commit',selected.upstream_commit],['Kaynak Git blob',selected.artifact_git_blob],['Manifest Git blob',selected.manifest_git_blob],['Manifest SHA-256',selected.manifest_sha256],['Kaynak SHA-256',selected.artifact_sha256],['Giriş şeması SHA-256',selected.input_schema_sha256],['Çıkış şeması SHA-256',selected.output_schema_sha256],['Kaynak bayt',String(selected.source_bytes)],['Lisans incelemesi',selected.license_ref],['Custody',selected.custody_ref],['Manifest yolu',`candidates/W5-EXT-05/catalog/${selected.skill_id}/manifest.json`],['G7 / G8','Yok · HOLD'],['Grant / dispatch / etkin araç','Yok · DENY'],['Kurulum kanıtı',selected.installation_evidence],['Bağımsız kabul','HOLD']
   ].map(([k,v])=><div key={k}><dt>{k}</dt><dd><code>{v}</code></dd></div>)}</dl>
   <h4>Rol bazlı tanısal inceleme</h4>{selected.reviews.map(r=><p key={r.role_hint} className="sub">{c.roles[r.role_hint as keyof typeof c.roles].label} · {r.reason} · {r.diagnostic_overlap.join(', ')} (tanısal, kayıtlı araç değil)</p>)}
   <h4>Tarihsel test kanıtı</h4><p>{selected.evidence.summary}</p><p className="sub">{selected.evidence.limitation}</p><p className={styles.wrap}><code>{selected.evidence.path}</code> · Git blob <code>{selected.evidence.git_blob}</code></p>
  </section>}
  <div className="eds-evidence"><div><strong>EXT-05 · {c.shared_evidence.python} · Şema {c.shared_evidence.schemas}</strong><small>Yerel sentetik katalog ve Gateway testleri; bağımsız kabul değil.</small><small className={styles.wrap}>{c.shared_evidence.path} · {c.shared_evidence.git_blob}</small></div><div><strong>Güvenlik kapıları: {c.shared_evidence.gates}</strong><small>Yükleme, etkinleştirme, grant, yürütme ve release kapalı.</small></div></div>
  <p className={styles.wrap}>Projeksiyon commit <code>{c.source_commit}</code> · Git blob <code>{c.projection_blob}</code></p>
 </section>;
}
