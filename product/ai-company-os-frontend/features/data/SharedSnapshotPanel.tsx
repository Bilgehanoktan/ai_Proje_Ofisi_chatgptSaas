"use client";
import {useSharedSnapshot} from './SharedSnapshotProvider';
import {useProjectionRead} from './useProjectionRead';
import {readStatus,type ReadState} from './projectionRead';
import {readSecurityView} from '../security/securityModel';

/** Existing CEO/Office shared historical view; no cross-reader joins or live authority. */
export default function SharedSnapshotPanel({office=false}:{office?:boolean}){
 const {state,read,reset,planRead}=useSharedSnapshot(),s=state.phase==='historical'?state.data:null,p=s?.prefix;
 const organization=useProjectionRead('organization');
 const plan=planRead.state.phase==='historical'?planRead.data:null;
 const org=organization.state.phase==='historical'?organization.data:null;
 const security=readSecurityView();
 const status=(value:ReadState<unknown>)=>readStatus(value,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Tarihsel D0 · HOLD',hold:'Okuma reddedildi · HOLD'});
 const trust=security.ok?security.trust:[];
 const iv=trust.find(item=>item.id==='iv')?.status??'HOLD',release=trust.find(item=>item.id==='release')?.status??'HOLD';
 return <section className="panel projection-summary" aria-label={office?'Office ortak tarihsel oturumu':'CEO ortak tarihsel oturumu'}><div className="bar"><div><div className="eyebrow">U2 / CEO + OFFICE / HISTORICAL ONLY</div><h2>Ortak görev gözlemi</h2></div><div className="chips"><button type="button" disabled={state.phase==='loading'} onClick={read}>Snapshot yeniden oku</button><button type="button" disabled={state.phase==='idle'} onClick={reset}>Ortak geçmişi temizle</button></div></div>
 <p role="status" data-phase={state.phase}>{state.phase==='historical'?'Tarihsel replay tamamlandı · HOLD':state.phase==='loading'?'Okunuyor…':state.phase==='hold'?'Geçersiz, süresi doldu veya bağlantı yok · HOLD':'Okunmadı · HOLD'}</p>
 {s&&p&&<><p className="sub">{p.tenant} / {p.company} / {p.environment} · run sırası #{s.snapshot_seq} · policy/W-A {p.policy_epoch}/{p.witness_epoch}</p><div className="projection-summary-grid"><article><small>Görev / run</small><strong>{p.task_id} / {p.run_id}</strong></article><article><small>Tarihsel durum</small><strong>{p.state}</strong></article><article><small>Örnek rezervasyon</small><strong>{p.sample_outstanding_minor} minor {p.currency}</strong></article><article><small>Gerçek aktif ajan</small><strong>—</strong></article></div><p className="sub" style={{overflowWrap:'anywhere'}}>Plan: {p.plan_revision} · agent referansı: {p.agent_instance_id} · proje ve world: kanıt yok · digest: {s.digest}</p></>}
 <p className="sub">Aynı uygulama oturumu; 30 sn görüntüleme süresi, gizlenmede veya ortak temizlemede tüm bağlı görünümlerden kaldırılır. Canlı SSE, ajan konumu, proje eşlemesi, gerçek KPI, harcama ve dispatch yok. Statik ofis geometrisi ayrı referanstır.</p>
 {!office&&<section className="panel" aria-label="CEO kaynak ve kontrol özeti">
  <div className="bar"><div><h3>Proje, organizasyon ve kontrol durumu</h3><small>Birbirinden bağımsız salt-okunur kanıtlar; atomik şirket anlık görüntüsü değil</small></div><span className="pill">HOLD / NO LIVE KPI</span></div>
  <div className="projection-summary-grid">
   <article aria-label="CEO proje planı"><h3>Proje / görev planı</h3><p role="status" data-phase={planRead.state.phase}>{status(planRead.state)}</p><strong>{plan?`${plan.tasks.length} referans görev · ${plan.waves.length} dalga`:'— · Gerçek görev yok'}</strong><small>{plan?'A0_SAMPLE_ONLY · gerçek tamamlanma bilinmiyor':'Onaylı canlı proje verisi yok'}</small><div className="chips"><button type="button" onClick={planRead.read} disabled={planRead.state.phase==='loading'}>Plan kaydını oku</button><button type="button" onClick={planRead.reset} disabled={planRead.state.phase==='idle'}>Planı temizle</button></div></article>
   <article aria-label="CEO organizasyon kaydı"><h3>AI çalışanlar / organizasyon</h3><p role="status" data-phase={organization.state.phase}>{status(organization.state)}</p><strong>{org?`${org.positions.length} tarihsel pozisyon`:'— · Aktif ajan bilinmiyor'}</strong><small>{org?'Doluluk kaydı gerçek çalışan veya IAM grant değildir':'Gerçek kimlik, yetki ve çalışan durumu HOLD'}</small><div className="chips"><button type="button" onClick={organization.read} disabled={organization.state.phase==='loading'}>ORG kaydını oku</button><button type="button" onClick={organization.reset} disabled={organization.state.phase==='idle'}>ORG temizle</button></div></article>
   <article aria-label="CEO karar ve güvenlik sınırı"><h3>Kararlar / güvenlik / IV</h3><p role="status">Statik D0 kontrol kaynağı · kabul değil</p><strong>IV: {iv} · Yayın: {release}</strong><small>Gerçek karar talebi — · etkin H01 onayı — · bağımsız güvenlik kabulü HOLD</small><p className="sub">Güvenlik ve Karar Kutusu ayrıntıları mevcut sol menüdedir.</p></article>
   <article aria-label="CEO ofis ve workflow sınırı"><h3>Sanal ofis / Workflow</h3><p role="status">Statik geometri · JOIN_HOLD</p><strong>Gerçek konum ve aktif workflow —</strong><small>Plan, ORG ve ortak oturum ayrı kaynaktır; otomatik birleştirilmez.</small><p><a href="/office">Mevcut Sanal Ofis sayfasına geç</a></p></article>
  </div>
  <p className="sub">Bu özet işlem başlatmaz, dispatch veya harcama izni üretmez. Farklı endpoint sonuçları aynı tenant/anda olduğuna dair kanıt olmadan eşleştirilmez.</p>
 </section>}
 </section>;
}
