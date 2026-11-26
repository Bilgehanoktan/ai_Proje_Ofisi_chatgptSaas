import styles from './AgentRoleProfile.module.css';
type RoleProfile={id:string;name:string;department:string;description:string};
type TaskLink={id:string;label:string};
type ProfileTask=TaskLink&{predecessors:readonly TaskLink[];followers:readonly TaskLink[]};
/** Input is the validated reference plan's role context; never a runtime assignment. */
export function orderRoleTasks(tasks:readonly ProfileTask[],waves:readonly (readonly string[])[]){
 const order=new Map<string,number>();
 for(const [index,wave] of waves.entries())for(const id of wave)order.set(id,index+1);
 return tasks.map(task=>({...task,wave:order.get(task.id)??null})).sort((a,b)=>(a.wave??Infinity)-(b.wave??Infinity)||a.id.localeCompare(b.id));
}
export default function AgentRoleProfile({role,tasks,waves}:{role:RoleProfile;tasks:readonly ProfileTask[]|null;waves:readonly (readonly string[])[]}){
 const rows=tasks===null?null:orderRoleTasks(tasks,waves);
 const waveCount=rows===null||rows.some(t=>t.wave===null)?null:new Set(rows.flatMap(t=>t.wave===null?[]:[t.wave])).size;
 return <div className={styles.profile} aria-label="Rol profil ve plan görünümü" role="group">
  <div className={styles.header}><div><small>ROL PROFİLİ / STATİK ŞABLON</small><h3>{role.name} · {role.department}</h3><p>{role.description}</p></div><span className="pill">HOLD · Atama yok</span></div>
  <dl className={styles.stats}><div><dt>Referans görev</dt><dd>{rows===null?'—':rows.length}</dd></div><div><dt>Plan dalgası</dt><dd>{waveCount??'—'}</dd></div><div><dt>Gerçek aktif run</dt><dd>—</dd></div><div><dt>Etkin model / beceri</dt><dd>—</dd></div></dl>
  <section className={styles.plan} aria-label="Referans rol görev akışı"><h3>Referans plandaki rol görevleri</h3><p>Plan sırası · gerçekleşen iş veya görev geçmişi değildir.</p>
   {rows===null?<p role="status">Plan doğrulanamadı · HOLD</p>:rows.length===0?<p>Bu rol için referans görev yok.</p>:<ol>{rows.map(t=><li key={t.id}><div className={styles.taskHead}><span className={styles.wave}>{t.wave===null?'Dalga bilinmiyor':`Dalga ${t.wave}`}</span><strong>{t.label}</strong><small>HOLD</small></div><dl><div><dt>Ön koşullar</dt><dd>{t.predecessors.map(p=>p.label).join(' · ')||'Yok'}</dd></div><div><dt>Ardıl görevler</dt><dd>{t.followers.map(p=>p.label).join(' · ')||'Yok'}</dd></div></dl></li>)}</ol>}
  </section>
  <p className={styles.boundary}>Gerçek görev ataması, çalışan kimliği, model, beceri, maliyet ve bağımsız kanıt doğrulanmadı. Aşağıdaki ayrı rol ayrıntısında bulunan tarihsel Runtime kaydı bu role ait geçmiş olarak kabul edilmez.</p>
 </div>;
}
