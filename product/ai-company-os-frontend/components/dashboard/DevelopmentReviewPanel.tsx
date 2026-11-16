"use client";
import ProjectStudio from '../../features/project-management/ProjectStudio';
import TaskBudgetPanel from '../../features/mvp/TaskBudgetPanel';

const stages = [
 ['Plan','Orchestrator'],['Gereksinim','Research'],['Kaynak adayı','Engineer'],
 ['Kalite','QA'],['Güvenlik','Security'],['Kanıt','Independent Verifier'],['Kapı incelemesi','Policy Review']
] as const;

export default function DevelopmentReviewPanel({mode='all'}:{mode?:'all'|'review'}={}){
 return <>{mode==='all'&&<ProjectStudio/>}<section className="panel"><h2>Research görev örneği</h2><p className="sub">Ayrı D0 kayıt okuması · DAG çalıştırması veya kanonik durum eşlemesi değil.</p><TaskBudgetPanel/></section><section className="panel" aria-label="Geliştirme inceleme merkezi">
  <div className="bar"><div><div className="eyebrow">DEVELOPMENT REVIEW / D0</div><h2>Ajan geliştirme merkezi</h2></div><span className="pill">STATIC_ONLY · HOLD</span></div>
  <p className="sub">Ayrı statik geliştirme inceleme senaryosu (Research planı değildir) · 7 görev · 6 dalga · QA ve Security paralel. Gerçek ajan yürütmesi, imzalı kanıt veya etkin yetki yok.</p>
  <div className="sectiongrid">{stages.map(([task,role])=><article className="item" key={role}><h3>{task}</h3><p>{role}</p><div className="status">NOT_RUN</div></article>)}</div>
  <div className="layout-hold" role="status"><strong>Kaynak inceleme: HOLD</strong><span>Kimlik, politika ve kalıcı kanıt altyapısı kaynak adayıdır. Bu ekran canlı veriye bağlı değildir; hiçbir işlem veya onay başlatmaz.</span></div>
 </section></>;
}
