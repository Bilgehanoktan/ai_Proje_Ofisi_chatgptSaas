import {historicalPresentation} from './historicalPresentation';
import {historicalAgentContext} from './studioContext';
export default function HistoricalEvidenceStrip({sample}:{sample:unknown}){
 const view=historicalPresentation(sample);
 if(!view)return <p role="status">Tarihsel kanıt yok · HOLD</p>;
 const {evidence}=view;
 const agent=historicalAgentContext();
 return <div className="projection-summary" aria-label="Tarihsel kayıt kapsamı">
   <div className="bar"><div><strong>{evidence.profile==='TERMINAL_SAMPLE'?'Terminal kayıt':'Ara kayıt'}</strong><p className="sub">HISTORICAL_SAMPLE · {evidence.run} · {view.recordLabel} (iş ilerlemesi değil)</p></div><small>{view.liveLabel}</small></div>
   <div className="projection-summary-grid" role="list">{evidence.slots.map(s=><article role="listitem" key={s.version} className="item"><small>v{s.version}</small><strong>{s.state??'Gözlenmedi'}</strong><small>{s.kind??'Bu örnekte kayıt yok'}</small></article>)}</div>
   <dl className="prefix-facts"><div><dt>Örnek kimliği</dt><dd>{view.sampleIdentity}</dd></div><div><dt>Veri kapsamı</dt><dd>{view.scope}</dd></div><div><dt>Görev / plan revizyonu</dt><dd>{view.task} · <code style={{overflowWrap:'anywhere'}}>{view.revision}</code></dd></div><div><dt>{view.budgetLabel}</dt><dd>{view.budgetValue}</dd></div><div><dt>Lease</dt><dd>{view.leaseLabel}</dd></div></dl>
   <p className="sub">Gerçek aktif run: {view.runCountLabel} · Ofis yerleşimi: {view.placementLabel} · Bağımsız kabul: {view.independentLabel} · Yayın: {view.releaseLabel}. Ayrı örnekler birleştirilmez. {agent.agentLabel} · {agent.runLabel} · {agent.decision}.</p>
 </div>;
}
