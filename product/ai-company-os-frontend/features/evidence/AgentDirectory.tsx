"use client";
import {useState} from 'react';
import type {Role} from '../../components/dashboard/AgentDetail';
import {RoleButton} from '../../components/dashboard/AgentDetail';
import {roleDirectory} from './evidenceModel';
import {readPlanProjection} from '../core-review/planProjection';
import {roleTaskContext} from './studioContext';
import styles from './EvidenceStudio.module.css';
export default function AgentDirectory({roles,selected,onSelect}:{roles:readonly Role[];selected:string|undefined;onSelect:(role:Role)=>void}){
 const [query,setQuery]=useState(''),[department,setDepartment]=useState(''),[sort,setSort]=useState(false);
 const filtered=roleDirectory(roles,query,department);
 const rows=sort?[...filtered].sort((a,b)=>a.id.localeCompare(b.id)):filtered;
 const selectedRole=roles.find(r=>r.id===selected),plan=readPlanProjection();
 const templateTasks=selectedRole&&plan.ok?roleTaskContext(plan.plan.tasks,selectedRole.id):[];
 const departments=[...new Set(roles.map(r=>r.department))].sort();
 const hidden=!!selectedRole&&!rows.some(r=>r.id===selectedRole.id);
 return <section className={styles.directory} aria-label="Agent Studio">
  <header className={styles.agentHero}><div><div className="eyebrow">AGENT STUDIO / D0</div><h2>Organizasyon ve rol kataloğu</h2><small>İnsan CEO nihai otorite · statik şablonlar · raporlama hiyerarşisi kanıtı yok</small></div><span className="pill">RESERVED · HOLD</span></header>
  <div className={styles.agentStats} aria-label="Rol kataloğu özeti"><div><small>Rol şablonu</small><strong>{roles.length}</strong></div><div><small>Departman şablonu</small><strong>{departments.length}</strong></div><div><small>Gerçek aktif çalışan</small><strong>—</strong></div><div><small>Etkin yetki</small><strong>HOLD</strong></div></div>
  <div className={styles.filters}><label>Rol ara<input type="search" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Departman<select value={department} onChange={e=>setDepartment(e.target.value)}><option value="">Tümü</option>{departments.map(d=><option key={d}>{d}</option>)}</select></label><button type="button" aria-pressed={sort} onClick={()=>setSort(v=>!v)}>Rol kimliğine göre sırala</button><button type="button" onClick={()=>{setQuery('');setDepartment('');setSort(false);}}>Temizle</button></div>
  <p role="status">{rows.length}/{roles.length} rol şablonu · gerçek instance yok</p>
  {hidden&&<p className={styles.notice} role="status">Seçili rol filtre dışında; bağlam korunuyor. <button type="button" onClick={()=>{setQuery('');setDepartment('');}}>Seçili rolü göster</button></p>}
  <div className="agentgrid">{rows.map(r=><RoleButton key={r.id} role={r} pressed={selected===r.id} onSelect={()=>onSelect(r)}/>)}</div>{rows.length===0&&<p className="empty">Eşleşen rol bulunamadı.</p>}
  {selectedRole&&<section className={styles.eventDetail} aria-label="Seçili rol şablonu"><div className="bar"><div><strong>{selectedRole.name}</strong><small>{selectedRole.department} · {selectedRole.id}</small></div><button type="button" onClick={()=>{setQuery('');setDepartment(selectedRole.department);}}>Departmanı göster</button></div><small>Rol şablonu · gerçek instance yok</small><small>Departmandaki şablon sayısı: {roles.filter(r=>r.department===selectedRole.department).length}</small>
   <h3>Referans plandaki rol görevleri</h3>{plan.ok?<>{templateTasks.length?<div className={styles.agentTasks}>{templateTasks.map(t=><article key={t.id}><strong>{t.label} · HOLD</strong><dl><div><dt>Ön koşullar</dt><dd>{t.predecessors.map(p=>p.label).join(' · ')||'Yok'}</dd></div><div><dt>Ardıl görevler</dt><dd>{t.followers.map(p=>p.label).join(' · ')||'Yok'}</dd></div></dl></article>)}</div>:<small>Bu rol için referans görev yok.</small>}<small>Statik plan ilişkisi · gerçek görev ataması veya yönetim hiyerarşisi değildir.</small></>:<small>Plan doğrulanamadı · HOLD</small>}
  </section>}
 </section>;
}
