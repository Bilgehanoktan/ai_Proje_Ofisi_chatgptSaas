"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import {parseMvpDiagnostics} from '../mvp/mvpDiagnostics';
export default function CapabilityReadback(){
 const {state,data,read}=useProjectionRead('mvp',parseMvpDiagnostics);
 return <section className="panel projection-summary" aria-label="Model, beceri ve hafıza incelemesi"><div className="bar"><div><div className="eyebrow">CAPABILITY / D0</div><h2>Model, Skill ve Memory Studio</h2><small>Salt okunur tanılama · sağlayıcı veya tool çağrısı yok</small></div><button type="button" onClick={read}>Tanılamayı oku</button></div><p role="status" className="projection-read-status" data-phase={state.phase}>{readStatus(state,{idle:'Okunmadı · HOLD',loading:'Okunuyor…',historical:'Sentetik tanılama · DENY',hold:'Tanılama doğrulanamadı · HOLD'})}</p><div className="sectiongrid">{(['model','gateway','tools'] as const).map(k=><article className="item" key={k}><h3>{k}</h3><p>{data?.sections[k]??'—'}</p><small>Tanılama · gerçek etkinlik değil</small></article>)}<article className="item"><h3>Kurumsal hafıza</h3><p>0196-MA kaynak adayı · UI API yok</p><small>ACL / witness / release HOLD · içerik veya retrieval sonucu gösterilmez</small></article></div><p className="sub">Model rezervasyon binding ve gerçek ToolGateway yetkisi ayrıca doğrulanmalıdır. Bu ekran hiçbir işlem başlatmaz.</p></section>;
}
