import type {ProjectView} from './projectModel';
import styles from './ProjectRoadmap.module.css';
/** Logical waves only; no duration, critical path, progress or runtime inference. */
export function roadmapFacts(view:ProjectView){
 const waves=view.groups.map((tasks,i)=>({number:i+1,tasks,parallel:tasks.length>1}));
 return {waves,parallelWaves:waves.filter(w=>w.parallel).length,gates:view.gates,planned:view.rows.length,hold:view.holdCount};
}
export default function ProjectRoadmap({view,selected,onSelect}:{view:ProjectView;selected:string;onSelect:(id:string)=>void}){
 const facts=roadmapFacts(view);
 return <section className={styles.root} aria-label="Proje planı ve teslimat kapıları">
  <div className={styles.header}><div><small>PROJECT ROADMAP / REFERENCE</small><h3>Proje yol haritası</h3><p>Tek doğrulanmış referans plan · portföy kaydı değil</p></div><span className="pill">RELEASE HOLD</span></div>
  <dl className={styles.metrics}><div><dt>Paralel plan dalgası</dt><dd>{facts.parallelWaves}</dd></div><div><dt>HOLD plan görevleri</dt><dd>{facts.hold}/{facts.planned}</dd></div><div><dt>Gerçek tamamlanma</dt><dd>—</dd></div><div><dt>Gerçek teslimat</dt><dd>—</dd></div></dl>
  <p className={styles.note}>Mantıksal sıra; tarih, süre, kritik yol veya gerçekleşen ilerleme değildir. Filtrelerden bağımsız tüm plan.</p>
  <ol className={styles.waves} aria-label="Referans dalga sırası">{facts.waves.map(w=><li key={w.number}><div className={styles.waveLabel}>Dalga {w.number} <small>{w.parallel?'Paralel plan':'Tek görev'}</small></div><div className={styles.tasks}>{w.tasks.map(t=><button type="button" key={t.id} aria-pressed={selected===t.id} onClick={()=>onSelect(t.id)}><strong>{t.label}</strong><small>{t.role} · {t.state}</small></button>)}</div></li>)}</ol>
  <div className={styles.gates} aria-label="Referans teslimat kapıları" role="group">{facts.gates.map(({task,wave})=><button type="button" key={task.id} aria-pressed={selected===task.id} onClick={()=>onSelect(task.id)}><strong>{task.label}</strong><small>Dalga {wave} · {task.role} · HOLD</small></button>)}</div>
  <p className={styles.note}>QA, bağımsız IV ve insan yayın yetkisi ayrı kapılardır. Gerçek kabul, çıktı veya teslimat kanıtı yok.</p>
 </section>;
}
