/** Presentation of a single parser-validated historical record; never joins sources. */
export type Fact={label:string;value:string};
const scalar=(v:unknown)=>typeof v==='string'||typeof v==='number'||typeof v==='boolean'?String(v):'—';
const fields:Record<string,readonly (readonly [string,string])[]>={
 mvp:[['plan_digest','Örnek plan özeti'],['sample_event_rows','Örnek olay satırı'],['diagnostic_remaining_minor','Tanısal kalan (minor)']],
 admission:[['phase','Örnek durum'],['version','Revizyon'],['sample_reserved_minor','Örnek rezervasyon (minor)'],['sample_observed_minor','Örnek gözlem (minor)'],['sample_remaining_minor','Örnek kalan (minor)']],
 outbox:[['phase','Örnek durum'],['generation','Nesil'],['readback_recorded','Okuma kaydı']],
 'office-workbench':[['sample_event_count','Örnek olay sayısı']],
 'task-budget':[['pair_id','Örnek çift kimliği'],['research_event_seq','Research olay sırası']],
 lifecycle:[['state','Tarihsel durum'],['run_id','Örnek run'],['task_id','Örnek görev']],
 'lifecycle-prefix':[['state','Tarihsel durum'],['run_id','Örnek run'],['task_id','Örnek görev'],['head_version','Revizyon'],['lease_freshness','Lease güncelliği'],['geometry_join','Konum bağı'],['model_binding','Model bağı'],['memory_acl','Memory ACL']]
};
export function readbackFacts(key:string,phase:string,raw:unknown):Fact[]{
 if(phase!=='historical'||!Object.hasOwn(fields,key)||!raw||typeof raw!=='object'||Array.isArray(raw))return [];
 const data=raw as Record<string,unknown>;
 return fields[key].filter(([k])=>Object.hasOwn(data,k)).map(([k,label])=>({label,value:scalar(data[k])}));
}
