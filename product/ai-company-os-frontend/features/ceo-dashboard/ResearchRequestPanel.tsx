"use client";
import {useId,useState} from 'react';
import {useSharedSnapshot} from '../data/SharedSnapshotProvider';
import {readStatus} from '../data/projectionRead';
import {parsePlanProjection} from '../core-review/planProjection';

/** H01-MVP03-01: select only the reviewed fixed D0 plan; no write or authorization. */
export default function ResearchRequestPanel(){
 const {planRead}=useSharedSnapshot();
 const state=planRead.state;
 // No fallback to offline fixture, no join to historical ORG or runtime data.
 const plan=state.phase==='historical'?parsePlanProjection(state.data):null;
 return <section className="panel projection-summary" aria-label="RESEARCH görev talebi">
  <div className="bar"><div><div className="eyebrow">CEO / MVP-03</div><h2>RESEARCH görev talebi</h2><small>H01-MVP03-01 · sabit plan kapsamı · D0 kaynak incelemesi</small></div><span className="pill">PERSISTENCE HOLD</span></div>
  <p role="status" data-phase={state.phase}>{state.phase==='historical'&&!plan?'Plan pini uyuşmadı · HOLD':readStatus(state,{idle:'Plan okunmadı · HOLD',loading:'Plan okunuyor…',historical:'Sabit plan referansı doğrulandı · D0',hold:'Plan okunamadı · HOLD'})}</p>
  <div className="chips" role="group" aria-label="RESEARCH plan okuma işlemleri">
   <button type="button" disabled={state.phase==='loading'} onClick={planRead.read}>RESEARCH planını oku</button>
   <button type="button" disabled={state.phase==='idle'} onClick={planRead.reset}>RESEARCH planını temizle</button>
  </div>
  {plan?<FixedPlanSelection key={plan.revision} plan={plan}/>:<p className="sub">Plan seçimi için mevcut backend plan okuyucusundan geçerli referans alınmalı. Eski veya çevrimdışı veri seçilemez.</p>}
  <div className="sectiongrid">
   <article className="item"><h3>Gönderim koşulları</h3><p>Yetkili HUMAN kimliği ve proje izni · HOLD</p><p>Project/WorkItem kalıcı eşlemesi ve idempotency · HOLD</p><p>Korumalı COMMIT ve bağımsız güvenlik · HOLD</p><button type="button" disabled>Görev talebini gönder</button><small>HTTP 201 yalnız doğrulanmış kalıcı kayıt sonrasında; HTTP 202 ayrı admission işlemidir.</small></article>
   <article className="item"><h3>Kalıcı kayıt geri okuması</h3><p role="status">Talep kaydı oluşturulmadı · request ID yok</p><button type="button" disabled>Talep kaydını oku</button><small>Yetkili request ID sorgusu henüz etkin değil. Plan veya geçmiş run kimliği talep kimliği değildir.</small></article>
  </div>
  <p className="sub">Yerel plan seçimi izin, kalıcı kayıt, dispatch, model çağrısı veya ajan yürütmesi başlatmaz. Bu yüzey ağ üzerinden yalnız mevcut salt-okunur plan okuyucusunu kullanır.</p>
 </section>;
}

function FixedPlanSelection({plan}:{plan:NonNullable<ReturnType<typeof parsePlanProjection>>}){
 const [selected,setSelected]=useState(false);
 const id=useId();
 return <fieldset aria-label="İncelenmiş RESEARCH planı">
  <legend>Sabit plan seçimi</legend>
  <label htmlFor={id}><input id={id} type="checkbox" checked={selected} onChange={e=>setSelected(e.target.checked)}/> Bu RESEARCH planını talep taslağı için seç</label>
  <p><strong>{plan.worktype} · {plan.plan_id}</strong> · {plan.tasks.length} referans görev</p>
  <p className="sub" style={{overflowWrap:'anywhere'}}>Revizyon: <code>{plan.revision}</code></p>
  <p role="status">{selected?'Plan seçildi · yalnız yerel taslak · gönderim HOLD':'Plan henüz seçilmedi'}</p>
  <small>Plan okuması temizlendiğinde, geçersizleştiğinde veya süresi dolduğunda seçim kaldırılır. Proje/tenant yetkisi doğrulanmadı.</small>
 </fieldset>;
}
