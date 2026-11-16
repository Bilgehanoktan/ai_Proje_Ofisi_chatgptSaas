/** Bounded local undo history; all new edges pass the original DAG validator. */
import {reviewDraft,type DraftTask,type DraftEdge} from './draftGraph';
export type DraftHistory={edges:DraftEdge[];past:DraftEdge[][];future:DraftEdge[][];message:string};
export type DraftAction={kind:'add';edge:DraftEdge}|{kind:'remove';edge:DraftEdge}|{kind:'undo'}|{kind:'redo'}|{kind:'reset'};
export const emptyDraftHistory=():DraftHistory=>({edges:[],past:[],future:[],message:''});
export function editDraft(tasks:readonly DraftTask[],current:DraftHistory,action:DraftAction):DraftHistory{
 if(action.kind==='reset')return {...emptyDraftHistory(),message:'Taslak sıfırlandı'};
 if(action.kind==='redo'){
  if(!current.future.length)return {...current,message:'İleri alınacak taslak değişikliği yok'};
  const edges=current.future[current.future.length-1],review=reviewDraft(tasks,edges);
  return review.ok?{edges,past:[...current.past,current.edges].slice(-20),future:current.future.slice(0,-1),message:'Taslak değişikliği ileri alındı · HOLD'}:{...emptyDraftHistory(),message:review.reason+' · Taslak sıfırlandı'};
 }
 if(action.kind==='undo'){
  if(!current.past.length)return {...current,message:'Geri alınacak taslak değişikliği yok'};
  const edges=current.past[current.past.length-1],review=reviewDraft(tasks,edges);
  return review.ok?{edges,past:current.past.slice(0,-1),future:[...current.future,current.edges].slice(-20),message:'Son taslak değişikliği geri alındı · HOLD'}:{...emptyDraftHistory(),message:review.reason+' · Taslak sıfırlandı'};
 }
 const next=action.kind==='add'?[...current.edges,{...action.edge}]:current.edges.filter(e=>e.from!==action.edge.from||e.to!==action.edge.to);
 if(action.kind==='remove'&&next.length===current.edges.length)return {...current,message:'Taslak bağlantı bulunamadı'};
 const review=reviewDraft(tasks,next);
 if(!review.ok)return {...current,message:review.reason+' · Taslak değişmedi'};
 return {edges:next,past:[...current.past,current.edges].slice(-20),future:[],message:'Yerel taslak güncellendi · HOLD'};
}
