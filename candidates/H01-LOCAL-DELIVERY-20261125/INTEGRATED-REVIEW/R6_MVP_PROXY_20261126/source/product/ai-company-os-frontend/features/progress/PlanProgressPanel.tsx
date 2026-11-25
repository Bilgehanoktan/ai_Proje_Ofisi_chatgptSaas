"use client";
import data from './w1PlanProgress.json';
import {summarizePlan} from './progressModel';
export default function PlanProgressPanel(){
 const p=summarizePlan(data);
 if(!p)return <section className="panel" aria-label="Plan ilerlemesi"><p role="status">İlerleme verisi uyumsuz · HOLD</p></section>;
 return <section className="panel plan-progress" aria-label="W1 A–H plan ilerlemesi"><div className="bar"><div><div className="eyebrow">{p.revision} / PLAN</div><h2>UI geliştirme planı</h2><small>Kaynak ve kanıt kilometre taşları · ürün kabulü değil</small></div><strong>%{p.percent} · {p.done}/{p.total}</strong></div><progress aria-label="W1 kilometre taşı oranı" max={p.total} value={p.done}/><div className="plan-progress-grid">{p.rows.map(l=><article key={l.id}><h3>{l.id} · {l.name}</h3><p>%{l.percent} · {l.done}/{l.total}</p><progress aria-label={l.name} max={l.total} value={l.done}/><details><summary>Kanıt ve açık işler</summary><ul>{l.gates.map(g=><li key={g.id}><strong>{g.id} · {g.status}</strong> {g.title}<small>{g.kind} · {g.evidence}</small></li>)}</ul></details></article>)}</div><p className="sub">Kapanmış kabul kilometre taşı: {p.accepted}. Bu oran eşit ağırlıklı 40 maddeye aittir, süre veya canlı ürün tamamlanması değildir.</p></section>;
}
