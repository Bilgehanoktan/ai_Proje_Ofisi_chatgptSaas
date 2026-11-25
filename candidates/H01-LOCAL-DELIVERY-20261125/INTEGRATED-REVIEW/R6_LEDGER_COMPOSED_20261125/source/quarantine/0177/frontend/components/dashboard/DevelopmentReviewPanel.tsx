"use client";

const stages = [
 ['Plan','Orchestrator'],['Gereksinim','Research'],['Kaynak adayı','Engineer'],
 ['Kalite','QA'],['Güvenlik','Security'],['Kanıt','Independent Verifier'],['Kapı incelemesi','Policy Review']
] as const;

export default function DevelopmentReviewPanel(){
 return <section className="panel" aria-label="Geliştirme inceleme merkezi">
  <div className="bar"><div><div className="eyebrow">DEVELOPMENT REVIEW / D0</div><h2>Ajan geliştirme merkezi</h2></div><span className="pill">STATIC_ONLY · HOLD</span></div>
  <p className="sub">7 görev · 6 dalga · QA ve Security paralel. Gerçek ajan yürütmesi, imzalı kanıt veya etkin yetki yok.</p>
  <div className="sectiongrid">{stages.map(([task,role])=><article className="item" key={role}><h3>{task}</h3><p>{role}</p><div className="status">NOT_RUN</div></article>)}</div>
  <div className="layout-hold" role="status"><strong>Kaynak inceleme: HOLD</strong><span>Kimlik, politika ve kalıcı kanıt altyapısı kaynak adayıdır. Bu ekran canlı veriye bağlı değildir; hiçbir işlem veya onay başlatmaz.</span></div>
 </section>;
}
