"use client";
import {useState} from 'react';
import {readFinanceView,financeMetricText} from './financeModel';
import ControlSourceInspector from '../evidence/ControlSourceInspector';
import styles from './FinanceStudio.module.css';
const tabs=[['overview','Finans özeti'],['saas','SaaS ve kota'],['goals','Tarihsel hedefler'],['sources','Kaynak ve kanıt']] as const;
type Tab=typeof tabs[number][0];
export default function FinanceStudio(){
 const [tab,setTab]=useState<Tab>('overview'),[selected,setSelected]=useState('available');
 const view=readFinanceView();
 if(!view.ok)return <section className="panel" role="alert">Finance Studio · HOLD · {view.reason}</section>;
 const detail=view.metrics.find(m=>m.id===selected);
 return <section className={`panel ${styles.studio}`} aria-label="Finans ve SaaS merkezi">
  <div className="bar"><div><div className="eyebrow">FINANCE / SAAS · D0</div><h2>Finance &amp; SaaS Command Center</h2><small>Sentetik kaynak görünümü · salt okunur</small></div><span className="pill">UNVERIFIED · NO SPEND</span></div>
  <div className={styles.banner}><strong>Doğrulanmış finansal veri mevcut değil</strong><span>— bilinmiyor anlamındadır, sıfır değildir. Tanısal kapasite yetkili bakiye olarak gösterilmez.</span></div>
  <div className="chips" role="group" aria-label="Finans görünümü">{tabs.map(([id,label])=><button type="button" key={id} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
  {tab==='overview'?<><div className={styles.metrics}>{view.metrics.map(m=><button type="button" key={m.id} aria-pressed={selected===m.id} className={styles.metric} onClick={()=>setSelected(m.id)}><span>{m.label}</span><strong>{financeMetricText(m.value)}</strong><small>{m.note}</small></button>)}</div><div className={styles.detail} aria-live="polite"><h3>{detail?.label??'Metrik seçilmedi'}</h3><small>Kaynak alanı</small><code>{detail?.source??'—'}</code><p>{detail?.note}</p><span>UNVERIFIED · Gerçek ekonomik olay veya yetki yok</span></div></>:tab==='saas'?<div className={styles.cards}>{view.saas.slice(0,2).map(r=><article className={styles.card} key={r.title}><h3>{r.title}</h3><p>{r.description}</p><small>{r.status}</small></article>)}<article className={styles.card}><h3>Kullanım ve faturalama</h3><p>Doğrulanmış kullanım, fatura veya ödeme kaydı yok.</p><small>UNVERIFIED · HOLD</small></article></div>:tab==='sources'?<ControlSourceInspector domain="finance"/>:<div className={styles.cards}>{view.goals.map(r=><article className={styles.card} key={r.title}><h3>{r.title}</h3><p>{r.description}</p><small>{r.status}</small></article>)}</div>}
  <div className={styles.boundary}><strong>Rezervasyon ≠ maliyet ≠ gelir ≠ tahsilat</strong><p>Gerçek bütçe, settlement, abonelik ve ödeme verileri için doğrulanmış backend projeksiyonu gerekir. Bu ekran işlem başlatmaz veya yetki vermez.</p></div>
 </section>;
}
