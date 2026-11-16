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

type Station=SnapshotFloor['stations'][number];
type Selection={floorId:string;stationId:string}|{roleId:string}|null;
const sections=catalog.sections as Record<string,{title:string;description:string;status:string}[]>;
const demoLayout=validateDemoLayout(core.layout);
const version='UI-P10B · D0 tarihsel veri okuması';
const layoutKey=`${fixture.layout_revision}:${core.layout.revision}`;
// Key resets all controlled presentation state when static layout or entry view changes.
export default function Dashboard({initialView}:{initialView:'overview'|'office'}){
 return <DashboardView key={`${initialView}:${layoutKey}`} initialView={initialView}/>;
}
function DashboardView({initialView}:{initialView:'overview'|'office'}){
 const officeOnly=initialView==='office';
 const [view,setView]=useState('Genel Bakış');
 const [floorId,setFloorId]=useState(fixture.floors[0].id);
 const [panel,setPanel]=useState<Panel>('Ajanlar');
 const [selected,setSelected]=useState<Selection>(null);
 const [detail,setDetail]=useState('Genel Bakış');
 const [display,setDisplay]=useState<Display>('scene');
 const currentView=officeOnly?'Sanal Ofis':view, overview=currentView==='Genel Bakış'||officeOnly;
 const floor=fixture.floors.find(f=>f.id===floorId);
 const demoFloor=demoLayout.ok?demoLayout.layout.floors.find(f=>f.id===floorId):undefined;
 const station=selected&&'stationId' in selected&&selected.floorId===floorId?floor?.stations.find(s=>s.id===selected.stationId):undefined;
 const role=ui.roles.find(r=>r.id===(selected&&'roleId' in selected?selected.roleId:station?.role_template_id));
 function resetContext(){setSelected(null);setDetail('Genel Bakış');setPanel('Ajanlar');}
 function changeFloor(id:string){if(id!==floorId&&fixture.floors.some(f=>f.id===id)){setFloorId(id);resetContext();}}
 function changeDisplay(d:Display){if(d!==display){setDisplay(d);resetContext();}}
 function navigate(name:string){if(name!==view){setView(name);resetContext();setDisplay('scene');}}
 function openStation(s:Station){if(!floor?.stations.some(x=>x.id===s.id)||!ui.roles.some(r=>r.id===s.role_template_id))return;setSelected({floorId,stationId:s.id});setPanel('Seçili Bağlam');setDetail('Genel Bakış');}
 function openRole(r:Role){setSelected({roleId:r.id});setPanel('Seçili Bağlam');setDetail('Genel Bakış');}
 function changeDetail(t:string){if(catalog.agent_detail_tabs.includes(t))setDetail(t);}
 function stationList(){return floor?.stations.length?<div className="station-list">{floor.stations.map(s=>{const r=ui.roles.find(x=>x.id===s.role_template_id);return r?<RoleButton key={s.id} role={r} pressed={station?.id===s.id} onSelect={()=>openStation(s)}/>:<div className="empty" key={s.id}>Bilinmeyen rol · HOLD · {s.id}</div>;})}</div>:<div className="empty">Bu katta istasyon yok. Yeni kat aktivasyonu veya ajan ataması yapılmadı.</div>;}
 const details=<AgentDetail role={role} context={station?`${floorId} / ${station.id}`:'Organizasyon rol şablonu · istasyon seçilmedi'} tabs={catalog.agent_detail_tabs} detail={detail} onDetail={changeDetail}/>;
 return <div className={`shell ${officeOnly?'shell-office':''}`}><a className="skip-link" href="#main-content">Ana içeriğe geç</a>
 {!officeOnly&&<aside className="sidebar"><div className="brand"><span className="mark">◈</span><div>AI COMPANY OS<small>D0 Studio · EDS / MVP</small></div></div><div className="navlabel">OPERASYON MERKEZİ</div><Navigation items={ui.nav.map(([name,icon])=>[name,icon] as const)} current={currentView} onNavigate={navigate}/><div className="profile"><span className="avatar">H01</span><div><strong>İnsan CEO</strong><small>Gözlem · salt-okunur</small></div></div></aside>}
 <main id="main-content" tabIndex={-1}><header className="topline"><div><div className="eyebrow">AI COMPANY / KONTROL MERKEZİ</div><h1>{currentView==='Genel Bakış'?'CEO Command Center':currentView}</h1><div className="sub">Tek insan CEO · dört çekirdek rol · {version}</div></div><div className="chips"><ThemeToggle/>{officeOnly&&<Link className="action-link" href="/">← CEO paneli</Link>}<span className="pill">D0 DEMO · SYNTHETIC_ONLY</span></div></header>
 <div className="notice">Sentetik görünüm. Gerçek ajan, görev, gelir, onay veya bağımsız kanıt yok. SOURCE_BOOTSTRAP_ONLY · LIVE_UNAUTHORIZED · T01 HOLD.</div>
 {overview?<><SnapshotStrip/>{!officeOnly&&<><MetricsStrip/><OperationalReadback/><LifecycleReadback context="ceo"/><LifecyclePrefixReadback context="ceo"/></>}<div className="workspace"><OfficePanel floors={fixture.floors} floorId={floorId} onFloor={changeFloor} display={display} onDisplay={changeDisplay} officeOnly={officeOnly} stations={stationList()} demoFloor={demoFloor} layoutRevision={String(core.layout.revision)} snapshotRevision={String(fixture.layout_revision)} geometryReason={demoLayout.ok?'Kat bulunamadı':demoLayout.reason}/><OperationPanel panel={panel} onPanel={setPanel} stations={stationList()} detail={details}/></div>{officeOnly&&<><LifecycleReadback key={"terminal-"+floorId} context="office"/><LifecyclePrefixReadback key={floorId} context="office"/></>}</>:currentView==='AI Çalışanlar'?<section className="panel"><h2>Çekirdek rol şablonları</h2><div className="agentgrid">{ui.roles.map(r=><RoleButton key={r.id} role={r} pressed={role?.id===r.id} onSelect={()=>openRole(r)}/>)}</div>{details}</section>:<section className="panel"><h2>{currentView} · Durum kataloğu</h2><div className="sectiongrid">{presentCatalogRows(currentView,sections,ui.sections).map(x=><article className="item" key={x.title}><h3>{x.title}</h3><p>{x.description}</p><div className="status">{x.status}</div></article>)}</div></section>}
 {!officeOnly&&(overview||['İş ve Denetim','Güvenlik','Olaylar'].includes(currentView))&&<CorePreview/>}
 {!officeOnly&&overview&&<MvpDiagnosticsPanel/>}
 {!officeOnly&&overview&&<WorkbenchLifecyclePanel/>}
 {!officeOnly&&overview&&<OutboxProjectionPanel/>}
 {!officeOnly&&overview&&<AdmissionProjectionPanel/>}
 {!officeOnly&&currentView==='İş ve Denetim'&&<><DevelopmentReviewPanel/><WorkflowDraft/><LifecycleReadback context="workflow"/><LifecyclePrefixReadback context="workflow"/></>}
 {!officeOnly&&currentView==='SaaS ve Finans'&&<><FinanceStudio/><AdmissionProjectionPanel/><LifecycleReadback context="finance"/><LifecyclePrefixReadback context="finance"/></>}
 {!officeOnly&&['Güvenlik','Raporlar'].includes(currentView)&&<><SecurityStudio key={currentView} initialTab={currentView==='Raporlar'?'evidence':'controls'}/><OutboxProjectionPanel key={currentView}/><LifecycleReadback key={currentView} context="security"/><LifecyclePrefixReadback key={"prefix-"+currentView} context="security"/></>}
 {!officeOnly&&currentView==='Beceriler'&&<><CapabilityReadback/><LifecyclePrefixReadback context="capability"/></>}
 {officeOnly&&<OfficeDecorPanel key={floorId}/>}
 <ProjectionReadbackCenter key={currentView+':'+(currentView==='Sanal Ofis'?floorId:'')} view={currentView}/>
 {!officeOnly&&overview&&<PlanProgressPanel/>}
 {!officeOnly&&<section className="panel bottom"><div className="bar"><h2>Geliştirme çalışma hatları</h2><span className="sub">Kaynak adayı · kabul edilmedi</span></div><div className="lanegrid">{catalog.lanes.map(x=><div className="lane" key={x.id}><strong>{x.id}</strong>{x.title}<small>{x.scope}</small></div>)}</div></section>}
 <footer>v135 hedef mimari · {version} · A0_SAMPLE_ONLY · NO_RELEASE · ACCEPTANCE HOLD</footer></main></div>;
}
