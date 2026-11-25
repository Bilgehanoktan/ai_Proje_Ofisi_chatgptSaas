"use client";
import {useState} from 'react';
import type {Role} from '../../components/dashboard/AgentDetail';
import {RoleButton} from '../../components/dashboard/AgentDetail';
import {roleDirectory} from './evidenceModel';
import {readPlanProjection} from '../core-review/planProjection';
import {roleTaskContext} from './studioContext';
import {organizationTemplate} from './studioGovernance';
import styles from './EvidenceStudio.module.css';
import OrganizationReadback from '../organization/OrganizationReadback';
import AgentRoleProfile from './AgentRoleProfile';
export default function AgentDirectory({roles,selected,onSelect}:{roles:readonly Role[];selected:string|undefined;onSelect:(role:Role)=>void}){
 const [query,setQuery]=useState(''),[department,setDepartment]=useState(''),[sort,setSort]=useState(false);
 const filtered=roleDirectory(roles,query,department);
 const rows=sort?[...filtered].sort((a,b)=>a.id.localeCompare(b.id)):filtered;
 const selectedRole=roles.find(r=>r.id===selected),plan=readPlanProjection();
 const templateTasks=selectedRole&&plan.ok?roleTaskContext(plan.plan.tasks,selectedRole.id):[];
 const departments=[...new Set(roles.map(r=>r.department))].sort();
 const organization=organizationTemplate(roles);
 const hidden=!!selectedRole&&!rows.some(r=>r.id===selectedRole.id);
 return <section className={styles.directory} aria-label="Agent Studio">
  <header className={styles.agentHero}><div><div className="eyebrow">AGENT STUDIO / D0</div><h2>Organizasyon ve rol kataloğu</h2><small>İnsan CEO nihai otorite · statik şablonlar · raporlama hiyerarşisi kanıtı yok</small></div><span className="pill">RESERVED · HOLD</span></header>
  <div className={styles.agentStats} aria-label="Rol kataloğu özeti"><div><small>Rol şablonu</small><strong>{roles.length}</strong></div><div><small>Departman şablonu</small><strong>{departments.length}</strong></div><div><small>Gerçek aktif çalışan</small><strong>—</strong></div><div><small>Etkin yetki</small><strong>HOLD</strong></div></div>
  <section className="panel" aria-label="Organizasyon hedef mimarisi"><h3>Organizasyon merkezi · hedef şablon</h3>{organization?<><div className="sectiongrid"><article className="item"><h3>H01 · İnsan CEO</h3><small>Nihai karar otoritesi</small></article><article className="item"><h3>{organization.coordinator.name}</h3><small>Mantıksal operasyon koordinasyonu</small></article>{organization.groups.map(g=><article className="item" key={g.department}><h3>{g.department}</h3>{g.roles.map(r=><p key={r.id}>{r.name} · rol şablonu</p>)}</article>)}</div><p className="sub">Ayrı güven kökleri: {organization.independent.join(" · ")}. QA, bağımsız IV değildir. Gerçek personel, raporlama ataması veya grant doğrulanmadı.</p></>:<p role="status">Rol kataloğu uyuşmuyor · HOLD</p>}</section>
  <OrganizationReadback/>
  <div className={styles.filters}><label>Rol ara<input type="search" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Departman<select value={department} onChange={e=>setDepartment(e.target.value)}><option value="">Tümü</option>{departments.map(d=><option key={d}>{d}</option>)}</select></label><button type="button" aria-pressed={sort} onClick={()=>setSort(v=>!v)}>Rol kimliğine göre sırala</button><button type="button" onClick={()=>{setQuery('');setDepartment('');setSort(false);}}>Temizle</button></div>
  <p role="status">{rows.length}/{roles.length} rol şablonu · gerçek instance yok</p>
  {hidden&&<p className={styles.notice} role="status">Seçili rol filtre dışında; bağlam korunuyor. <button type="button" onClick={()=>{setQuery('');setDepartment('');}}>Seçili rolü göster</button></p>}
  <div className="agentgrid">{rows.map(r=><RoleButton key={r.id} role={r} pressed={selected===r.id} onSelect={()=>onSelect(r)}/>)}</div>{rows.length===0&&<p className="empty">Eşleşen rol bulunamadı.</p>}
  {selectedRole&&<section className={styles.eventDetail} aria-label="Seçili rol şablonu"><div className="bar"><div><strong>{selectedRole.name}</strong><small>{selectedRole.department} · {selectedRole.id}</small></div><button type="button" onClick={()=>{setQuery('');setDepartment(selectedRole.department);}}>Departmanı göster</button></div><small>Rol şablonu · gerçek instance yok</small><small>Departmandaki şablon sayısı: {roles.filter(r=>r.department===selectedRole.department).length}</small>
   <AgentRoleProfile role={selectedRole} tasks={plan.ok?templateTasks:null} waves={plan.ok?plan.plan.waves:[]}/>
  </section>}
 </section>;
}
