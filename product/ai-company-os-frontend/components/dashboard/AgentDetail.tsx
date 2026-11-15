"use client";
import type ui from '../../features/uiCatalog.json';
import {rolePortraitUri,roleVisual} from '../../design-system/roleVisuals';
export type Role = typeof ui.roles[number];
const sections:Readonly<Record<string,readonly [string,string][]>>={
 'Beceriler ve Şablonlar':[['Beceri kaydı','Doğrulanmış beceri ataması yok'],['Şablon','Yalnız statik rol tanımı']],
 'Görevler ve DAG':[['Görev','Gerçek görev bağlantısı yok'],['Yürütme','HOLD · dispatch yok']],
 'Yetkiler ve Güvenlik':[['Grant','Yok'],['Politika','DENY · bağımsız kabul HOLD']],
 'Model ve Çalıştırma':[['Model','Atanmamış'],['Runtime','Gerçek instance yok']],
 'Maliyet ve Kullanım':[['Token','— · veri yok'],['Maliyet','— · muhasebe kaydı yok']],
 'QA, Kanıt ve Audit':[['QA','Gerçek sonuç yok'],['IV / Release','Bağımsız kanıt yok · HOLD']]
};
export function RoleButton({role,pressed,onSelect}:{role:Role;pressed:boolean;onSelect:()=>void}) {
 return <button type="button" className="role" aria-pressed={pressed} onClick={onSelect}><img src={rolePortraitUri(role.id)} width={44} height={44} alt="" style={{flexShrink:0,borderRadius:12}}/><span><strong>{role.name}</strong><small>{role.department} · Rol şablonu</small></span><span className="end">REZERV</span></button>;
}
export default function AgentDetail({role,context,tabs,detail,onDetail}:{role:Role|undefined;context:string;tabs:readonly string[];detail:string;onDetail:(tab:string)=>void}) {
 if(!role)return <div className="empty" role="status">Bir istasyon veya rol seçin. Seçili ajan yok.</div>;
 const visual=roleVisual(role.id);
 const rows=detail==='Genel Bakış'?[['Departman',role.department],['Sorumluluk',role.description],['Tip','Rol şablonu · fiziksel çalışan değil']]:sections[detail]??[['Durum','Bilinmeyen sekme · HOLD']];
 return <section className="detail" aria-label="Rol ayrıntısı"><div className="bar"><div style={{display:'flex',alignItems:'center',gap:12,minWidth:0}}><img src={rolePortraitUri(role.id)} width={64} height={64} alt="" style={{flexShrink:0,borderRadius:16}}/><div><h3>{role.name} · Rol detayı</h3><div className="sub">{visual?.motif??'Görsel kimlik yok'} · Rol portresi</div><div className="context-id">{context}</div></div></div><span className="pill">REZERV / HOLD</span></div><div className="tabs" aria-label="Rol ayrıntıları">{tabs.map(t=><button type="button" key={t} aria-pressed={detail===t} onClick={()=>onDetail(t)}>{t}</button>)}</div><div className="empty" aria-live="polite"><strong>{detail}</strong><dl>{rows.map(([k,v])=><div key={k}><dt><small>{k}</small></dt><dd style={{margin:'0 0 8px',overflowWrap:'anywhere'}}>{v}</dd></div>)}</dl><small>Instance: yok · Grant: yok · Kanıt: yok</small></div></section>;
}
