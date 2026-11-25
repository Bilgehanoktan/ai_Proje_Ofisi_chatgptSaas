export type AdmissionProjection={phase:'PENDING'|'RESERVED'|'SETTLED_SAMPLE'|'UNKNOWN_HOLD';version:number;sample_reserved_minor:number;sample_observed_minor:number;sample_remaining_minor:number};
const keys=['schema_version','mode','tenant','company','phase','version','sample_reserved_minor','sample_observed_minor','sample_remaining_minor','admission','dispatch_allowed','spend_allowed','release_ready','actual_cost_minor','authoritative'];
const states={PENDING:[0,0,0,1000],RESERVED:[1,100,0,900],SETTLED_SAMPLE:[2,0,60,940],UNKNOWN_HOLD:[2,100,0,900]} as const;
export function parseAdmissionProjection(x:unknown):AdmissionProjection|null{
 if(!x||typeof x!=='object'||Array.isArray(x))return null;
 const v=x as Record<string,unknown>;
 if(Object.keys(v).length!==keys.length||!keys.every(k=>Object.hasOwn(v,k)))return null;
 if(v.schema_version!=='admission.sample.v1-D0'||v.mode!=='D0_ADMISSION_STORE_0186'||v.tenant!=='synthetic-tenant'||v.company!=='synthetic-company'||v.admission!=='DENY'||v.actual_cost_minor!==null||['dispatch_allowed','spend_allowed','release_ready','authoritative'].some(k=>v[k]!==false))return null;
 const p=v.phase;if(typeof p!=='string'||!Object.hasOwn(states,p))return null;
 const phase=p as keyof typeof states,[version,reserved,observed,remaining]=states[phase];
 if(v.version!==version||v.sample_reserved_minor!==reserved||v.sample_observed_minor!==observed||v.sample_remaining_minor!==remaining)return null;
 return {phase,version,sample_reserved_minor:reserved,sample_observed_minor:observed,sample_remaining_minor:remaining};
}
