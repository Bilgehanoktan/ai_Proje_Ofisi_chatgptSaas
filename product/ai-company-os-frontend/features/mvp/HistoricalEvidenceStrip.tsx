import {historicalEvidence} from './historicalEvidence';
export default function HistoricalEvidenceStrip({sample}:{sample:unknown}){
 const evidence=historicalEvidence(sample);
 if(!evidence)return <p role="status">Tarihsel kanıt yok · HOLD</p>;
 return <div className="projection-summary" aria-label="Tarihsel kayıt kapsamı">
   <div className="bar"><div><strong>{evidence.profile==='TERMINAL_SAMPLE'?'Terminal kayıt':'Ara kayıt'}</strong><p className="sub">HISTORICAL_SAMPLE · {evidence.run} · {evidence.observed}/5 kayıt adımı (iş ilerlemesi değil)</p></div><small>CANLI VERİ DEĞİL</small></div>
   <div className="projection-summary-grid" role="list">{evidence.slots.map(s=><article role="listitem" key={s.version} className="item"><small>v{s.version}</small><strong>{s.state??'Gözlenmedi'}</strong><small>{s.kind??'Bu örnekte kayıt yok'}</small></article>)}</div>
   <p className="sub">Gerçek aktif run: bilinmiyor · Ofis yerleşimi: HOLD · Bağımsız kabul: HOLD. Ayrı örnekler birleştirilmez.</p>
 </div>;
}
