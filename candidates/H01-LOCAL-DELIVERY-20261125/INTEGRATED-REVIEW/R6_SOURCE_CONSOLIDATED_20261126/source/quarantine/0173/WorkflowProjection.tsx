export type Wave={id:string;label:string;nodes:readonly {id:string;label:string;state:string}[]};
export default function WorkflowProjection({waves}:{waves:readonly Wave[]}){
 return <section className="eds-card"><h2>Görev DAG · salt okunur</h2><p>Sentetik plan projeksiyonu; yürütme veya görev kabulü yok.</p><div className="eds-waves">{waves.map(w=><section key={w.id}><h3>{w.label}</h3><ul>{w.nodes.map(n=><li key={n.id}>{n.label}<small>{n.state}</small></li>)}</ul></section>)}</div></section>;
}
