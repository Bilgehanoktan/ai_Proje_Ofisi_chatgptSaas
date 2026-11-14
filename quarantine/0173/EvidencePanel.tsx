export type EvidenceRow={id:string;label:string;state:'HOLD'|'UNKNOWN'|'NOT_RUN'|'STATIC_ONLY';detail:string};
export default function EvidencePanel({rows}:{rows:readonly EvidenceRow[]}){
 return <section className="eds-card" aria-label="Kanıt sınırları"><h2>Kanıt ve güvenlik</h2><ul className="eds-evidence">{rows.map(r=><li key={r.id}><strong>{r.label}</strong><span>{r.state}</span><small>{r.detail}</small></li>)}</ul></section>;
}
