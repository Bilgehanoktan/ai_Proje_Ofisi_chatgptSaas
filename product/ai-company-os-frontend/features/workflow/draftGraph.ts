/** Local design sandbox only. Never modifies the pinned plan or grants execution. */
export type DraftTask={id:string;depends_on:readonly string[]};
export type DraftEdge={from:string;to:string};
export type DraftReview={ok:true;waves:string[][]}|{ok:false;reason:string};
export function reviewDraft(tasks:readonly DraftTask[],added:readonly DraftEdge[]):DraftReview{
 const hold=(reason:string):DraftReview=>({ok:false,reason});
 if(tasks.length<1||tasks.length>100||added.length>200)return hold('DRAFT_LIMIT');
 const ids=new Set(tasks.map(t=>t.id));
 if(ids.size!==tasks.length||tasks.some(t=>!(/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$/).test(t.id)))return hold('TASK_ID');
 const deps=new Map<string,Set<string>>();
 for(const t of tasks){const d=new Set(t.depends_on);if(d.size!==t.depends_on.length||[...d].some(x=>!ids.has(x)||x===t.id))return hold('BASE_EDGE');deps.set(t.id,d);}
 for(const e of added){if(!ids.has(e.from)||!ids.has(e.to)||e.from===e.to)return hold('EDGE_ENDPOINT');const d=deps.get(e.to)!;if(d.has(e.from))return hold('DUPLICATE_EDGE');d.add(e.from);}
 const remaining=new Set(ids),waves:string[][]=[];
 while(remaining.size){const wave=[...remaining].filter(id=>[...deps.get(id)!].every(d=>!remaining.has(d))).sort();if(!wave.length)return hold('CYCLE');waves.push(wave);for(const id of wave)remaining.delete(id);}
 return {ok:true,waves};
}
