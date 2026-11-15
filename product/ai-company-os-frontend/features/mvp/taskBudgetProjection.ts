import {parseAdmissionProjection,type AdmissionProjection} from './admissionProjection';
import {parseOfficeWorkbench,type OfficeWorkbench} from './officeWorkbenchProjection';
const fixed={schema_version:'task.budget.snapshot.v1-D0',mode:'D0_PAIRED_SAMPLE_0188',tenant:'synthetic-tenant',company:'synthetic-company',plan_digest:'6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9',task_id:'research',run_id:'demo-run',sample_budget_ref:'demo-budget',consistency:'STABLE_DOUBLE_READ_NOT_ATOMIC',freshness:'HISTORICAL_SAMPLE',causality:'UNPROVEN',lease_binding:'HOLD',geometry_join:'HOLD',dispatch_allowed:false,spend_allowed:false,release_ready:false,authoritative:false} as const;
const keys=[...Object.keys(fixed),'pair_id','workbench_event_seq','research_event_seq','admission_version','sample_admission_ref','office','budget'];
export type TaskBudgetProjection={pair_id:string;research_event_seq:3|null;office:OfficeWorkbench;budget:AdmissionProjection};
export function parseTaskBudgetProjection(x:unknown):TaskBudgetProjection|null{
 if(!x||typeof x!=='object'||Array.isArray(x))return null;
 const v=x as Record<string,unknown>;
 if(Object.keys(v).length!==keys.length||!keys.every(k=>Object.hasOwn(v,k))||Object.entries(fixed).some(([k,val])=>v[k]!==val))return null;
 if(typeof v.pair_id!=='string'||v.pair_id.length!==32||!/^[0-9a-f]{32}$/.test(v.pair_id))return null;
 const office=parseOfficeWorkbench(v.office),budget=parseAdmissionProjection(v.budget);
 if(!office||!budget)return null;
 const research_event_seq=office.sample_event_count>=3?3:null;
 if(v.workbench_event_seq!==office.sample_event_count||v.research_event_seq!==research_event_seq||v.admission_version!==budget.version||v.sample_admission_ref!==(budget.version?'demo-admission':null))return null;
 return {pair_id:v.pair_id,research_event_seq,office,budget};
}
