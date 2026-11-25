/** Derived design-only data; the original DAG validator remains authoritative for drafts. */
import {reviewDraft,type DraftTask,type DraftEdge} from './draftGraph';
export type InspectorTask=DraftTask&{label:string;role:string};
export function inspectDraft(tasks:readonly InspectorTask[],edges:readonly DraftEdge[],selected:string){
 const review=reviewDraft(tasks,edges);
 if(!review.ok)return null;
 const task=tasks.find(t=>t.id===selected);
 if(!task)return null;
 const labels=new Map(tasks.map(t=>[t.id,t.label]));
 const all=[...tasks.flatMap(t=>t.depends_on.map(from=>({from,to:t.id,kind:'reference' as const}))),...edges.map(e=>({...e,kind:'draft' as const}))];
 const links=all.filter(e=>e.from===selected||e.to===selected).map(e=>({...e,direction:e.to===selected?'incoming' as const:'outgoing' as const,peer:e.to===selected?e.from:e.to,label:labels.get(e.to===selected?e.from:e.to)??''}));
 return {task,wave:review.waves.findIndex(w=>w.includes(selected))+1,links};
}
export function previewDraftEdge(tasks:readonly DraftTask[],edges:readonly DraftEdge[],from:string,to:string){
 if(!from||!to)return {phase:'idle'} as const;
 const base=reviewDraft(tasks,edges);
 if(!base.ok)return {phase:'hold',reason:base.reason} as const;
 const candidate=reviewDraft(tasks,[...edges,{from,to}]);
 return candidate.ok?{phase:'valid',before:base.waves.length,after:candidate.waves.length} as const:{phase:'hold',reason:candidate.reason} as const;
}
