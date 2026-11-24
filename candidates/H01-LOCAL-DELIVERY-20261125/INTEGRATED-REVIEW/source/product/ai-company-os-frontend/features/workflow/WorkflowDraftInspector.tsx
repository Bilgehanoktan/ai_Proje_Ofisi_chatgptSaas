"use client";
import {inspectDraft,previewDraftEdge,type InspectorTask} from './draftInspector';
import type {DraftHistory} from './draftHistory';
import type {DraftEdge} from './draftGraph';
import styles from './DraftInspector.module.css';
export default function DraftInspector({tasks,draft,selected,from,to,onSelect,onSource,onTarget,onRemove}:{tasks:readonly InspectorTask[];draft:DraftHistory;selected:string;from:string;to:string;onSelect:(id:string)=>void;onSource:(id:string)=>void;onTarget:(id:string)=>void;onRemove:(edge:DraftEdge)=>void}){
 const info=inspectDraft(tasks,draft.edges,selected),preview=previewDraftEdge(tasks,draft.edges,from,to);
 return <section className={styles.root} aria-label="Workflow düğüm denetçisi">
  <div className={styles.head}><div><small>WORKFLOW / DESIGN ONLY</small><h3>Düğüm denetçisi</h3></div><span className="pill">DRAFT · HOLD</span></div>
  <dl className={styles.stats}><div><dt>Geri alma</dt><dd>{draft.past.length}/20</dd></div><div><dt>İleri alma</dt><dd>{draft.future.length}/20</dd></div><div><dt>Ek bağlantı</dt><dd>{draft.edges.length}</dd></div></dl>
  <label className={styles.select}>İncelenen görev<select value={selected} onChange={e=>onSelect(e.target.value)}><option value="">Görev seçin</option>{tasks.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label>
  {info?<><div className={styles.identity}><strong>{info.task.label}</strong><small>{info.task.id} · {info.task.role} · Taslak dalga {info.wave} · HOLD</small><div className="chips"><button type="button" onClick={()=>onSource(info.task.id)}>Ön koşul olarak seç</button><button type="button" onClick={()=>onTarget(info.task.id)}>Bağımlı olarak seç</button></div></div>
  <div className={styles.links}>{(['incoming','outgoing'] as const).map(direction=><section key={direction} aria-label={direction==='incoming'?'Gelen bağlantılar':'Giden bağlantılar'}><h4>{direction==='incoming'?'Gelen bağlantılar':'Giden bağlantılar'}</h4>{info.links.filter(l=>l.direction===direction).length===0?<small>Bağlantı yok</small>:<ul>{info.links.filter(l=>l.direction===direction).map(l=><li key={JSON.stringify([l.from,l.to])}><button type="button" onClick={()=>onSelect(l.peer)}>{l.label}</button><small>{l.kind==='reference'?'Referans · kilitli':'Yerel taslak'}</small>{l.kind==='draft'&&<button type="button" aria-label={'Taslak bağlantıyı kaldır: '+l.from+' → '+l.to} onClick={()=>onRemove({from:l.from,to:l.to})}>Taslağı kaldır</button>}</li>)}</ul>}</section>)}</div></>:<p className={styles.note}>Görev seçilmedi veya taslak doğrulanamadı · HOLD</p>}
  <div className={styles.preview} aria-label="Bağlantı ön kontrolü" role="group"><strong>Bağlantı ön kontrolü</strong><p>{preview.phase==='idle'?'İki uç seçin.':preview.phase==='hold'?preview.reason+' · Taslak değişmedi':'Yerel DAG geçerli · dalga '+preview.before+' → '+preview.after+' · Henüz eklenmedi'}</p><small>Ön kontrol kayıt değildir; ekleme sırasında mevcut doğrulayıcı tekrar çalışır.</small></div>
  <p className={styles.note}>Kanonik plan, gerçek görev ataması, model, süre, dispatch ve release değiştirilmez.</p>
 </section>;
}
