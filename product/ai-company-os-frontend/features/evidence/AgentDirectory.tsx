"use client";
import {useState} from 'react';
import type {Role} from '../../components/dashboard/AgentDetail';
import {RoleButton} from '../../components/dashboard/AgentDetail';
import {roleDirectory} from './evidenceModel';
import styles from './EvidenceStudio.module.css';
export default function AgentDirectory({roles,selected,onSelect}:{roles:readonly Role[];selected:string|undefined;onSelect:(role:Role)=>void}){
 const [query,setQuery]=useState(''),[department,setDepartment]=useState('');
 const rows=roleDirectory(roles,query,department);
 return <div className={styles.directory}><div className={styles.filters}><label>Rol ara<input type="search" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Departman<select value={department} onChange={e=>setDepartment(e.target.value)}><option value="">Tümü</option>{[...new Set(roles.map(r=>r.department))].sort().map(d=><option key={d}>{d}</option>)}</select></label><button type="button" onClick={()=>{setQuery('');setDepartment('');}}>Temizle</button></div><p role="status">{rows.length}/{roles.length} rol şablonu · gerçek instance yok</p><div className="agentgrid">{rows.map(r=><RoleButton key={r.id} role={r} pressed={selected===r.id} onSelect={()=>onSelect(r)}/>)}</div>{rows.length===0&&<p className="empty">Eşleşen rol bulunamadı.</p>}</div>;
}
