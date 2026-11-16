"use client";
import {useState} from 'react';
import type {Role} from '../../components/dashboard/AgentDetail';
import {RoleButton} from '../../components/dashboard/AgentDetail';
import {roleDirectory} from './evidenceModel';
import styles from './EvidenceStudio.module.css';
export default function AgentDirectory({roles,selected,onSelect}:{roles:readonly Role[];selected:string|undefined;onSelect:(role:Role)=>void}){
 const [query,setQuery]=useState(''),[department,setDepartment]=useState(''),[sort,setSort]=useState(false);
 const filtered=roleDirectory(roles,query,department);
 const rows=sort?[...filtered].sort((a,b)=>a.id.localeCompare(b.id)):filtered;
 const hidden=!!selected&&roles.some(r=>r.id===selected)&&!rows.some(r=>r.id===selected);
 return <div className={styles.directory}><div className={styles.filters}><label>Rol ara<input type="search" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Departman<select value={department} onChange={e=>setDepartment(e.target.value)}><option value="">Tümü</option>{[...new Set(roles.map(r=>r.department))].sort().map(d=><option key={d}>{d}</option>)}</select></label><button type="button" aria-pressed={sort} onClick={()=>setSort(v=>!v)}>Rol kimliğine göre sırala</button><button type="button" onClick={()=>{setQuery('');setDepartment('');setSort(false);}}>Temizle</button></div><p role="status">{rows.length}/{roles.length} rol şablonu · gerçek instance yok</p>{hidden&&<p className={styles.notice} role="status">Seçili rol filtre dışında; bağlam korunuyor. <button type="button" onClick={()=>{setQuery('');setDepartment('');}}>Seçili rolü göster</button></p>}<div className="agentgrid">{rows.map(r=><RoleButton key={r.id} role={r} pressed={selected===r.id} onSelect={()=>onSelect(r)}/>)}</div>{rows.length===0&&<p className="empty">Eşleşen rol bulunamadı.</p>}</div>;
}
