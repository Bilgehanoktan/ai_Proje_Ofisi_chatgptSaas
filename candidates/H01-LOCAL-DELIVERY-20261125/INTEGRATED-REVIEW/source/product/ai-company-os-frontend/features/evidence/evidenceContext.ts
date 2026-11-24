/** Read-only evidence context. No live identity, time, or cross-source joins. */
import {parseLifecycleProjection} from '../mvp/lifecycleProjection';
import {parseLifecyclePrefix} from '../mvp/lifecyclePrefix';
import {reviewTimeline} from './evidenceReview';
export type ContextField={label:string;value:string};
export function evidenceContext(endpoint:string,phase:string,data:unknown):{key:string;fields:ContextField[]}|null{
 if(phase!=='historical')return null;
 const p=endpoint==='lifecycle'?parseLifecycleProjection(data):endpoint==='lifecycle-prefix'?parseLifecyclePrefix(data):null;
 if(!p)return null;
 const fields=[{label:'Örnek plan revizyonu',value:p.plan_revision},{label:'Örnek görev / run',value:p.task_id+' / '+p.run_id},{label:'Kayıt sürümü',value:String(p.head_version)},{label:'Nedensellik',value:p.causality},{label:'Konum bağı',value:p.geometry_join},{label:'Bağımsız kabul',value:p.independent_acceptance}];
 if('model_binding' in p)fields.push({label:'Model bağı',value:p.model_binding},{label:'Memory ACL',value:p.memory_acl},{label:'Lease güncelliği',value:p.lease_freshness});
 return {key:endpoint+':'+p.plan_revision+':'+p.run_id+':'+p.head_version,fields};
}
export function selectedEvidenceEvent(endpoint:string,phase:string,data:unknown,query:string,state:string,newest:boolean,selection:{key:string;version:number}|null){
 const ctx=evidenceContext(endpoint,phase,data);
 if(!ctx||!selection||selection.key!==ctx.key)return null;
 return reviewTimeline(endpoint,phase,data,query,state,newest).rows.find(e=>e.version===selection.version)??null;
}
