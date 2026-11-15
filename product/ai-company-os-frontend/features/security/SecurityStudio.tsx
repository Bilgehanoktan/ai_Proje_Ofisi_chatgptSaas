"use client";
import {useId,useState} from 'react';
import {readSecurityView,filterReasons,type SecurityRow} from './securityModel';
import styles from './SecurityStudio.module.css';
const tabs=[['controls','Yetki ve kontroller'],['trust','Güven zinciri'],['evidence','Kanıt ve ret kodları']] as const;
type Tab=typeof tabs[number][0];
export default function SecurityStudio({initialTab='controls'}:{initialTab?:Tab}){
 const [tab,setTab]=useState<Tab>(initialTab),[selected,setSelected]=useState('normative'),[query,setQuery]=useState('');
 const searchId=useId(),view=readSecurityView();
 if(!view.ok)return <section className="panel" role="alert">Security Studio · HOLD · {view.reason}</section>;
 const detail=[...view.controls,...view.trust].find(r=>r.id===selected),reasons=filterReasons(view.reasons,query);
 const card=(r:SecurityRow)=><button type="button" key={r.id} className={styles.card} aria-pressed={selected===r.id} onClick={()=>setSelected(r.id)}><span>{r.label}</span><strong>{r.status}</strong><small>{r.note}</small></button>;
 return <section className={`panel ${styles.studio}`} aria-label="Güvenlik ve kanıt merkezi">
  <div className="bar"><div><div className="eyebrow">SECURITY / EVIDENCE · D0</div><h2>Security &amp; Evidence Command Center</h2><small>Salt okunur kaynak incelemesi</small></div><span className="pill">DENY · HOLD</span></div>
  <div className={styles.banner}><strong>Bağımsız kabul kapıları kapalı</strong><span>CEO-0174 / CEO-0179=B çalışma kapsamı, normatif CODE / REPO / DEV veya gerçek ajan grant'i değildir.</span></div>
  <div className="chips" role="group" aria-label="Güvenlik görünümü">{tabs.map(([id,label])=><button type="button" key={id} aria-pressed={tab===id} onClick={()=>{setTab(id);setSelected(id==='controls'?'normative':id==='trust'?'policy':'');}}>{label}</button>)}</div>
  {tab==='controls'?<div className={styles.grid}>{view.controls.map(card)}</div>:tab==='trust'?<><p className="sub">Ayrı kontrol yüzeyleri; bu sıra bir yürütme veya geçiş kanıtı değildir.</p><div className={styles.trust}>{view.trust.map(card)}</div></>:<div className={styles.evidence}><h3>Sentetik ret nedenleri</h3><label htmlFor={searchId}>Kod ara<input id={searchId} type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="WA, F0, ACCEPTANCE…"/></label><small role="status">{reasons.length}/{view.reasons.length} kod</small>{reasons.length?<ul>{reasons.map(r=><li key={r}><code>{r}</code></li>)}</ul>:<p className="empty">Eşleşen kod yok.</p>}<p>Gerçek makbuz, imza, bağımsız doğrulanmış çıktı veya gerçek karar vakası yok. Kodlar canlı güvenlik olayı değildir.</p></div>}
  {tab!=='evidence'&&detail&&<div className={styles.detail} aria-live="polite"><h3>{detail.label}</h3><small>Kaynak / tasarım referansı</small><code>{detail.source}</code><p>{detail.note}</p></div>}
  <div className={styles.boundary}><strong>QA ≠ Independent Verifier ≠ Release</strong><p>Yerel yardımcı testler bağımsız güvenlik kabulü yerine geçmez. Üretim, harcama, sağlayıcı çağrısı ve gerçek dış etki yetkisizdir.</p></div>
 </section>;
}
