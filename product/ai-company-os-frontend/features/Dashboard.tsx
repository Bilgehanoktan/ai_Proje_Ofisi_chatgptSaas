"use client";
import {useState} from 'react';
import Link from 'next/link';
import CorePreview from './CorePreview';
import OfficeScene from '../office/OfficeScene';
import {validateDemoLayout} from '../office/geometry';
import core from '../fixtures/core.preview.json';
import fixture from '../fixtures/office.snapshot.json';
import catalog from '../fixtures/company.catalog.json';
import ui from './uiCatalog.json';

const panelTabs = ['Aktivite','Ajanlar','Onaylar','Seçili Bağlam'] as const;
type Panel = typeof panelTabs[number];
type Role = typeof ui.roles[number];
type Station = typeof fixture.floors[number]['stations'][number];
type Selection = {floorId:string; stationId:string} | {roleId:string} | null;
const sections = catalog.sections as Record<string,{title:string;description:string;status:string}[]>;
const officeAssets: Record<string,string> = {'floor-1':'/office-core.svg','floor-2':'/office-reserve.svg'};
const demoLayout = validateDemoLayout(core.layout);
const layoutMatches = String(fixture.layout_revision) === String(core.layout.revision);
const metricIcons = ['◈','▣','₺','◇'];

export default function Dashboard({initialView}:{initialView:'overview'|'office'}) {
  const officeOnly = initialView === 'office';
  const [view,setView] = useState('Genel Bakış');
  const [floorId,setFloorId] = useState(fixture.floors[0].id);
  const [panel,setPanel] = useState<Panel>('Ajanlar');
  const [selected,setSelected] = useState<Selection>(null);
  const [detail,setDetail] = useState('Genel Bakış');
  const [display,setDisplay] = useState<'scene'|'list'|'engine'>('scene');
  const currentView = officeOnly ? 'Sanal Ofis' : view;
  const overview = currentView === 'Genel Bakış' || officeOnly;
  const floor = fixture.floors.find(f=>f.id===floorId);
  const demoFloor = demoLayout.ok ? demoLayout.layout.floors.find(f=>f.id===floorId) : undefined;
  const station = selected && 'stationId' in selected && selected.floorId===floorId
    ? floor?.stations.find(s=>s.id===selected.stationId) : undefined;
  const roleId = selected && 'roleId' in selected ? selected.roleId : station?.role_template_id;
  const role = ui.roles.find(r=>r.id===roleId);

  function changeFloor(id:string) {
    if (!fixture.floors.some(f=>f.id===id)) return;
    setFloorId(id); setSelected(null); setDetail('Genel Bakış'); setPanel('Ajanlar');
  }
  function openStation(s:Station) {
    if (!floor?.stations.some(candidate=>candidate.id===s.id)) return;
    setSelected({floorId,stationId:s.id}); setPanel('Seçili Bağlam'); setDetail('Genel Bakış');
  }
  function openRole(r:Role) {
    setSelected({roleId:r.id}); setPanel('Seçili Bağlam'); setDetail('Genel Bakış');
  }
  function navigate(name:string) {
    setView(name); setSelected(null); setPanel('Ajanlar'); setDetail('Genel Bakış');
  }
  function roleButton(r:Role, s?:Station) {
    return <button className="role" key={s?.id??r.id} aria-pressed={s ? station?.id===s.id : role?.id===r.id} onClick={()=>s?openStation(s):openRole(r)}>
      <span className="avatar" style={{background:r.color}} aria-hidden="true">{r.initials}</span>
      <span><strong>{r.name}</strong><small>{r.department} · Rol şablonu</small></span><span className="end">REZERV</span>
    </button>;
  }
  function stationList() {
    if (!floor?.stations.length) return <div className="empty">Bu katta istasyon yok. Yeni kat aktivasyonu veya ajan ataması yapılmadı.</div>;
    return <div className="station-list">{floor.stations.map(s=>{
      const r=ui.roles.find(r=>r.id===s.role_template_id);
      return r ? roleButton(r,s) : <div className="empty" key={s.id}>Bilinmeyen rol · HOLD · {s.id}</div>;
    })}</div>;
  }
  function detailView() {
    if (!role) return <div className="empty" role="status">Bir istasyon veya rol seçin. Seçili ajan yok.</div>;
    return <div className="detail"><h3>{role.name} · Ajan detayı</h3>
      <div className="context-id">{station ? `${floorId} / ${station.id}` : 'Organizasyon rol şablonu · istasyon seçilmedi'}</div>
      <div className="tabs">{catalog.agent_detail_tabs.map(t=><button key={t} aria-pressed={detail===t} onClick={()=>setDetail(t)}>{t}</button>)}</div>
      <div className="empty"><strong>{detail}</strong><p>{detail==='Genel Bakış'?role.description:'Bu sekmede gerçek veri bulunmuyor.'}</p>Instance: yok · Grant: yok · Kanıt: yok</div>
    </div>;
  }
  function officePanel() {
    return <section className="panel office-panel" aria-label="Sanal ofis">
      <div className="bar"><div><div className="eyebrow">OFFICE-01 / GÖRSEL PROJEKSİYON</div><h2>Sanal ofis</h2><div className="sub">{floor?.name??'Kat bulunamadı'} · Statik kaynak</div></div>
        <div className="chips"><button aria-pressed={display==='scene'} onClick={()=>setDisplay('scene')}>Sahne</button><button aria-pressed={display==='engine'} onClick={()=>setDisplay('engine')}>Geometri stüdyosu</button><button aria-pressed={display==='list'} onClick={()=>setDisplay('list')}>Liste</button>{!officeOnly&&<Link className="action-link" href="/office">Tam ekran ↗</Link>}</div>
      </div>
      <div className="floor-switch" aria-label="Kat seçimi">{fixture.floors.map((f,i)=><button key={f.id} aria-pressed={floorId===f.id} onClick={()=>changeFloor(f.id)}><span>0{i+1}</span>{f.name}<small>{f.stations.length} istasyon</small></button>)}</div>
      {display==='scene'&&floor&&officeAssets[floor.id] ? <div className="scene"><img src={officeAssets[floor.id]} alt={`${floor.name} statik izometrik çizimi`}/><span className="corner">{floor.stations.length?`${floor.stations.length} rezerv istasyon`:'Genişleme rezervi'}</span></div> : display==='scene' ? <div className="empty">Bu kat için görsel kaynak yok.</div> : null}
      {display==='engine'&&(demoFloor ? <OfficeScene key={`${core.layout.revision}:${demoFloor.id}`} floor={demoFloor}/> : <div className="empty" role="status">Geometri HOLD · {demoLayout.ok?'Kat bulunamadı':demoLayout.reason}</div>)}
      <div className="station-heading"><h3>İstasyonlar</h3><span className="sub">Klavye ile seçilebilir · gerçek instance yok</span></div>
      {stationList()}
      <div className="layout-hold" role="status"><strong>Snapshot ↔ geometri entegrasyonu: HOLD</strong><span>{layoutMatches?'Sürüm adı eşleşiyor; bağımsız yerleşim kabulü henüz yok.':`Yerleşim revizyonları farklı: ${fixture.layout_revision} / ${core.layout.revision}.`} Konumlar birleştirilmedi; geometri stüdyosu yalnız ayrı demo katıdır.</span></div>
    </section>;
  }
  return <div className={`shell ${officeOnly?'shell-office':''}`}>
    <a className="skip-link" href="#main-content">Ana içeriğe geç</a>
    {!officeOnly&&<aside className="sidebar"><div className="brand"><span className="mark">◈</span><div>AI COMPANY OS<small>D0 Studio · draft.6 recovery</small></div></div><div className="navlabel">OPERASYON MERKEZİ</div>
      <nav aria-label="Ana navigasyon">{ui.nav.map(([n,i])=>n==='Sanal Ofis'?<Link className="nav-link" key={n} href="/office"><span className="navicon">{i}</span>{n}</Link>:n==='Genel Bakış'?<button key={n} aria-pressed={currentView===n} onClick={()=>navigate(n)}><span className="navicon">{i}</span>{n}</button>:<button key={n} aria-pressed={currentView===n} onClick={()=>navigate(n)}><span className="navicon">{i}</span>{n}</button>)}</nav>
      <div className="profile"><span className="avatar">H01</span><div><strong>İnsan CEO</strong><small>Gözlem · salt-okunur</small></div></div></aside>}
    <main id="main-content" tabIndex={-1}>
      <header className="topline"><div><div className="eyebrow">AI COMPANY / KONTROL MERKEZİ</div><h1>{currentView==='Genel Bakış'?'CEO Command Center':currentView}</h1><div className="sub">Tek insan CEO · dört çekirdek rol · genişleyebilir şirket</div></div><div className="chips">{officeOnly&&<Link className="action-link" href="/">← CEO paneli</Link>}<span className="pill">D0 DEMO · RUNTIME YOK</span></div></header>
      <div className="notice">⛨ &nbsp; Sentetik görünüm. Gerçek ajan, görev, gelir, onay veya bağımsız kanıt bulunmuyor. CODE/REPO/DEV etkin değil.</div>
      {overview?<>
        <div className="snapshot-strip" aria-label="Snapshot kaynak bilgileri"><span>Snapshot <strong>#{fixture.snapshot_seq}</strong></span><span>Tenant <strong>{fixture.tenant_id}</strong></span><span>World <strong>{fixture.world_id}</strong></span><span>Ortam <strong>{fixture.environment_id}</strong></span><span>Layout <strong>{fixture.layout_revision}</strong></span><span>As-of <time dateTime={fixture.as_of}>{fixture.as_of}</time></span><span>Policy / W-A <strong>{fixture.policy_epoch??'—'} / {fixture.wa_epoch??'—'}</strong></span><span>{fixture.data_status}</span></div>
        {!officeOnly&&<div className="metrics">{fixture.metrics.map((m,i)=><div className="metric" key={m.metric_id}><small>{metricIcons[i]} &nbsp; {m.label}</small><div className="value">{m.value??'—'}</div><small>Veri doğrulanmadı</small></div>)}</div>}
        <div className="workspace">{officePanel()}<section className="panel operation-panel"><div className="bar"><h2>Operasyon paneli</h2><span className="sub">SALT OKUNUR</span></div><div className="tabs">{panelTabs.map(t=><button key={t} aria-pressed={panel===t} onClick={()=>setPanel(t)}>{t}</button>)}</div>{panel==='Ajanlar'?stationList():panel==='Seçili Bağlam'?detailView():<div className="empty">{panel==='Onaylar'?'Gerçek karar yok · HOLD':'Gerçek olay akışı yok · UNKNOWN'}</div>}</section></div>
      </>:currentView==='AI Çalışanlar'?<section className="panel"><h2>Çekirdek rol şablonları</h2><div className="agentgrid">{ui.roles.map(r=>roleButton(r))}</div>{detailView()}</section>:<section className="panel"><h2>{currentView} · Durum kataloğu</h2><div className="sectiongrid">{(sections[currentView]??[]).map(x=><article className="item" key={x.title}><h3>{x.title}</h3><p>{x.description}</p><div className="status">{x.status}</div></article>)}</div></section>}
      {!officeOnly&&(overview||currentView==='İş ve Denetim'||currentView==='Güvenlik'||currentView==='Olaylar')&&<CorePreview/>}
      {!officeOnly&&<section className="panel bottom"><div className="bar"><h2>Geliştirme çalışma hatları</h2><span className="sub">Kaynak adayı · kabul edilmedi</span></div><div className="lanegrid">{catalog.lanes.map(x=><div className="lane" key={x.id}><strong>{x.id}</strong>{x.title}<small>{x.scope}</small></div>)}</div></section>}
      <footer>v135 hedef mimari · DOC-REV-0154 · Draft.6 Recovery · A0_SAMPLE_ONLY · NO_RELEASE · NOT_RUN</footer>
    </main></div>;
}
