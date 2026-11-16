"use client";
import {useState} from 'react';
import Link from 'next/link';
import Navigation from '../../design-system/Navigation';
import {ThemeToggle} from '../../design-system/ThemeFrame';
import {presentCatalogRows} from '../../design-system/catalogPresentation';
import CorePreview from '../core-review/CorePreview';
import {validateDemoLayout} from '../../office/engine/geometry';
import core from '../../fixtures/core.preview.json';
import fixture from '../../fixtures/office.snapshot.json';
import catalog from '../../fixtures/company.catalog.json';
import ui from '../uiCatalog.json';
import SnapshotStrip from '../../components/dashboard/SnapshotStrip';
import SharedSnapshotPanel from '../data/SharedSnapshotPanel';
import MetricsStrip from '../../components/dashboard/MetricsStrip';
import OfficePanel,{type Display,type SnapshotFloor} from '../../components/dashboard/OfficePanel';
import AgentDetail,{RoleButton,type Role} from '../../components/dashboard/AgentDetail';
import OperationPanel,{type Panel} from '../../components/dashboard/OperationPanel';
import DevelopmentReviewPanel from '../../components/dashboard/DevelopmentReviewPanel';
import FinanceStudio from '../finance/FinanceStudio';
import SecurityStudio from '../security/SecurityStudio';
import MvpDiagnosticsPanel from '../mvp/MvpDiagnosticsPanel';
import WorkbenchLifecyclePanel from '../mvp/WorkbenchLifecyclePanel';
import OutboxProjectionPanel from '../mvp/OutboxProjectionPanel';
import AdmissionProjectionPanel from '../mvp/AdmissionProjectionPanel';
import PlanProgressPanel from '../progress/PlanProgressPanel';
import OperationalReadback from './OperationalReadback';
import LifecyclePrefixReadback from '../mvp/LifecyclePrefixReadback';
import LifecycleReadback from '../mvp/LifecycleReadback';
import CapabilityReadback from '../capabilities/CapabilityReadback';
import WorkflowDraft from '../workflow/WorkflowDraft';
import ProjectionReadbackCenter from '../workflow/ProjectionReadbackCenter';
import OfficeDecorPanel from '../workflow/OfficeDecorPanel';
import AgentDirectory from '../evidence/AgentDirectory';
import ProjectStudio from '../project-management/ProjectStudio';
import SectionSwitcher from './SectionSwitcher';
import {ceoSections,workSections,type CeoSection,type WorkSection} from './sectionModel';

type Station=SnapshotFloor['stations'][number];
type Selection={floorId:string;stationId:string}|{roleId:string}|null;
const sections=catalog.sections as Record<string,{title:string;description:string;status:string}[]>;
const demoLayout=validateDemoLayout(core.layout);
const version='UI-P10J-13 · D0 ortak tarihsel bağlam';
const layoutKey=`${fixture.layout_revision}:${core.layout.revision}`;
// Key resets all controlled presentation state when static layout or entry view changes.
export default function Dashboard({initialView}:{initialView:'overview'|'office'}){
 return <DashboardView key={`${initialView}:${layoutKey}`} initialView={initialView}/>;
}
function DashboardView({initialView}:{initialView:'overview'|'office'}){
 const officeOnly=initialView==='office';
 const [view,setView]=useState('Genel Bakış');
 const [ceoSection,setCeoSection]=useState<CeoSection>('summary');
 const [workSection,setWorkSection]=useState<WorkSection>('projects');
 const [floorId,setFloorId]=useState(fixture.floors[0].id);
 const [panel,setPanel]=useState<Panel>('Ajanlar');
 const [selected,setSelected]=useState<Selection>(null);
 const [detail,setDetail]=useState('Genel Bakış');
 const [display,setDisplay]=useState<Display>('scene');
 const currentView=officeOnly?'Sanal Ofis':view, ceo=currentView==='Genel Bakış', work=currentView==='İş ve Denetim';
 const floor=fixture.floors.find(f=>f.id===floorId);
 const demoFloor=demoLayout.ok?demoLayout.layout.floors.find(f=>f.id===floorId):undefined;
 const station=selected&&'stationId' in selected&&selected.floorId===floorId?floor?.stations.find(s=>s.id===selected.stationId):undefined;
 const role=ui.roles.find(r=>r.id===(selected&&'roleId' in selected?selected.roleId:station?.role_template_id));
 function resetContext(){setSelected(null);setDetail('Genel Bakış');setPanel('Ajanlar');}
 function changeFloor(id:string){if(id!==floorId&&fixture.floors.some(f=>f.id===id)){setFloorId(id);resetContext();}}
 function changeDisplay(d:Display){if(d!==display){setDisplay(d);resetContext();}}
 function resetSections(){resetContext();setDisplay('scene');setFloorId(fixture.floors[0].id);}
 function navigate(name:string){if(name!==view){setView(name);setCeoSection('summary');setWorkSection('projects');resetSections();}}
 function changeCeoSection(id:CeoSection){if(id!==ceoSection){setCeoSection(id);resetSections();}}
 function changeWorkSection(id:WorkSection){if(id!==workSection){setWorkSection(id);resetSections();}}
 function openStation(s:Station){if(!floor?.stations.some(x=>x.id===s.id)||!ui.roles.some(r=>r.id===s.role_template_id))return;setSelected({floorId,stationId:s.id});setPanel('Seçili Bağlam');setDetail('Genel Bakış');}
 function openRole(r:Role){setSelected({roleId:r.id});setPanel('Seçili Bağlam');setDetail('Genel Bakış');}
 function changeDetail(t:string){if(catalog.agent_detail_tabs.includes(t))setDetail(t);}
 function stationList(){return floor?.stations.length?<div className="station-list">{floor.stations.map(s=>{const r=ui.roles.find(x=>x.id===s.role_template_id);return r?<RoleButton key={s.id} role={r} pressed={station?.id===s.id} onSelect={()=>openStation(s)}/>:<div className="empty" key={s.id}>Bilinmeyen rol · HOLD · {s.id}</div>;})}</div>:<div className="empty">Bu katta istasyon yok. Yeni kat aktivasyonu veya ajan ataması yapılmadı.</div>;}
 const details=<AgentDetail role={role} context={station?`${floorId} / ${station.id}`:'Organizasyon rol şablonu · istasyon seçilmedi'} tabs={catalog.agent_detail_tabs} detail={detail} onDetail={changeDetail}/>;
 return <div className={`shell ${officeOnly?'shell-office':''}`}><a className="skip-link" href="#main-content">Ana içeriğe geç</a>
 {!officeOnly&&<aside className="sidebar"><div className="brand"><span className="mark">◈</span><div>AI COMPANY OS<small>D0 Studio · EDS / MVP</small></div></div><div className="navlabel">OPERASYON MERKEZİ</div><Navigation items={ui.nav.map(([name,icon])=>[name,icon] as const)} current={currentView} onNavigate={navigate}/><div className="profile"><span className="avatar">H01</span><div><strong>İnsan CEO</strong><small>Gözlem · salt-okunur</small></div></div></aside>}
 <main id="main-content" tabIndex={-1}><header className="topline"><div><div className="eyebrow">AI COMPANY / KONTROL MERKEZİ</div><h1>{currentView==='Genel Bakış'?'CEO Command Center':currentView}</h1><div className="sub">Tek insan CEO · dört çekirdek rol · {version}</div></div><div className="chips"><ThemeToggle/>{officeOnly&&<Link className="action-link" href="/">← CEO paneli</Link>}<span className="pill">D0 DEMO · SYNTHETIC_ONLY</span></div></header>
 <div className="notice">Sentetik görünüm. Gerçek ajan, görev, gelir, onay veya bağımsız kanıt yok. SOURCE_BOOTSTRAP_ONLY · LIVE_UNAUTHORIZED · T01 HOLD.</div>
 {ceo&&<SectionSwitcher label="CEO bölümleri" options={ceoSections} current={ceoSection} onChange={changeCeoSection}/>}
 {work&&<SectionSwitcher label="İş ve Denetim bölümleri" options={workSections} current={workSection} onChange={changeWorkSection}/>}
 {(ceo||officeOnly)&&<SnapshotStrip/>}
 {ceo&&ceoSection==='summary'&&<><MetricsStrip/><OperationalReadback/><SharedSnapshotPanel/><section className="panel" aria-label="Yönetim bağlamı"><div className="bar"><h2>Şirket yönetim bağlamı</h2><span className="pill">D0 · HOLD</span></div><p className="sub">Dört çekirdek rol şablonu; etkin çalışan veya canlı departman performansı kanıtı değildir.</p><div className="sectiongrid">{ui.roles.map(r=><article className="item" key={r.id}><h3>{r.department}</h3><p>{r.name} · {r.description}</p><small>Rol şablonu · gerçek run bilinmiyor</small></article>)}</div><div className="chips"><button type="button" onClick={()=>navigate('Hedefler')}>Hedef kataloğu</button><button type="button" onClick={()=>navigate('Karar Kutusu')}>Karar kutusu</button></div></section></>}
 {(officeOnly||(ceo&&ceoSection==='operations'))&&<div className="workspace"><OfficePanel floors={fixture.floors} floorId={floorId} onFloor={changeFloor} display={display} onDisplay={changeDisplay} officeOnly={officeOnly} stations={stationList()} demoFloor={demoFloor} layoutRevision={String(core.layout.revision)} snapshotRevision={String(fixture.layout_revision)} geometryReason={demoLayout.ok?'Kat bulunamadı':demoLayout.reason}/><OperationPanel panel={panel} onPanel={setPanel} stations={stationList()} detail={details}/></div>}
 {ceo&&ceoSection==='operations'&&<WorkbenchLifecyclePanel/>}
 {officeOnly&&<><LifecycleReadback key={"terminal-"+floorId} context="office"/><LifecyclePrefixReadback key={floorId} context="office"/></>}
 {ceo&&ceoSection==='evidence'&&<><LifecycleReadback context="ceo"/><LifecyclePrefixReadback context="ceo"/><CorePreview/><MvpDiagnosticsPanel/><OutboxProjectionPanel/><AdmissionProjectionPanel/><ProjectionReadbackCenter key={currentView} view={currentView}/><PlanProgressPanel/><section className="panel bottom"><div className="bar"><h2>Geliştirme çalışma hatları</h2><span className="sub">Kaynak adayı · kabul edilmedi</span></div><div className="lanegrid">{catalog.lanes.map(x=><div className="lane" key={x.id}><strong>{x.id}</strong>{x.title}<small>{x.scope}</small></div>)}</div></section></>}
 {work&&workSection==='projects'&&<ProjectStudio/>}
 {work&&workSection==='workflow'&&<WorkflowDraft/>}
 {work&&workSection==='audit'&&<><section className="panel"><h2>{currentView} · Durum kataloğu</h2><div className="sectiongrid">{presentCatalogRows(currentView,sections,ui.sections).map(x=><article className="item" key={x.title}><h3>{x.title}</h3><p>{x.description}</p><div className="status">{x.status}</div></article>)}</div></section><CorePreview/><DevelopmentReviewPanel mode="review"/><LifecycleReadback context="workflow"/><LifecyclePrefixReadback context="workflow"/><ProjectionReadbackCenter key={currentView} view={currentView}/><section className="panel bottom"><div className="bar"><h2>Geliştirme çalışma hatları</h2><span className="sub">Kaynak adayı · kabul edilmedi</span></div><div className="lanegrid">{catalog.lanes.map(x=><div className="lane" key={x.id}><strong>{x.id}</strong>{x.title}<small>{x.scope}</small></div>)}</div></section></>}
 {!ceo&&!officeOnly&&!work&&(currentView==='AI Çalışanlar'?<section className="panel"><h2>Çekirdek rol şablonları</h2><AgentDirectory roles={ui.roles} selected={role?.id} onSelect={openRole}/>{details}</section>:<section className="panel"><h2>{currentView} · Durum kataloğu</h2><div className="sectiongrid">{presentCatalogRows(currentView,sections,ui.sections).map(x=><article className="item" key={x.title}><h3>{x.title}</h3><p>{x.description}</p><div className="status">{x.status}</div></article>)}</div></section>)}
 {!officeOnly&&['Güvenlik','Olaylar'].includes(currentView)&&<CorePreview/>}
 {!officeOnly&&currentView==='SaaS ve Finans'&&<><FinanceStudio/><AdmissionProjectionPanel/><LifecycleReadback context="finance"/><LifecyclePrefixReadback context="finance"/></>}
 {!officeOnly&&['Güvenlik','Raporlar'].includes(currentView)&&<><SecurityStudio key={currentView} initialTab={currentView==='Raporlar'?'evidence':'controls'}/><OutboxProjectionPanel key={currentView}/><LifecycleReadback key={currentView} context="security"/><LifecyclePrefixReadback key={"prefix-"+currentView} context="security"/></>}
 {!officeOnly&&currentView==='Beceriler'&&<><CapabilityReadback/><LifecyclePrefixReadback context="capability"/></>}
 {currentView==='Sanal Ofis'&&<OfficeDecorPanel key={floorId}/>}
 {!ceo&&!work&&<ProjectionReadbackCenter key={currentView+':'+(currentView==='Sanal Ofis'?floorId:'')} view={currentView}/>}
 {!officeOnly&&!ceo&&!work&&<section className="panel bottom"><div className="bar"><h2>Geliştirme çalışma hatları</h2><span className="sub">Kaynak adayı · kabul edilmedi</span></div><div className="lanegrid">{catalog.lanes.map(x=><div className="lane" key={x.id}><strong>{x.id}</strong>{x.title}<small>{x.scope}</small></div>)}</div></section>}
 <footer>v135 hedef mimari · {version} · A0_SAMPLE_ONLY · NO_RELEASE · ACCEPTANCE HOLD</footer></main></div>;
}
