"use client";
import type ui from '../../features/uiCatalog.json';
export type Role = typeof ui.roles[number];
export function RoleButton({role,pressed,onSelect}:{role:Role;pressed:boolean;onSelect:()=>void}) {
 return <button className="role" aria-pressed={pressed} onClick={onSelect}><span className="avatar" style={{background:role.color}} aria-hidden="true">{role.initials}</span><span><strong>{role.name}</strong><small>{role.department} · Rol şablonu</small></span><span className="end">REZERV</span></button>;
}
export default function AgentDetail({role,context,tabs,detail,onDetail}:{role:Role|undefined;context:string;tabs:readonly string[];detail:string;onDetail:(tab:string)=>void}) {
 if(!role)return <div className="empty" role="status">Bir istasyon veya rol seçin. Seçili ajan yok.</div>;
 return <div className="detail"><h3>{role.name} · Rol detayı</h3><div className="context-id">{context}</div><div className="tabs" aria-label="Rol ayrıntıları">{tabs.map(t=><button key={t} aria-pressed={detail===t} onClick={()=>onDetail(t)}>{t}</button>)}</div><div className="empty"><strong>{detail}</strong><p>{detail==='Genel Bakış'?role.description:'Bu sekmede gerçek veri bulunmuyor.'}</p>Instance: yok · Grant: yok · Kanıt: yok</div></div>;
}
