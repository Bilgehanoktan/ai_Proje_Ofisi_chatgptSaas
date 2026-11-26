/** A single existing parser's historical record, never a cross-record join or live KPI. */
import {parseLifecycleProjection} from '../mvp/lifecycleProjection';
import {parseLifecyclePrefix} from '../mvp/lifecyclePrefix';
export type EvidenceEvent={version:number;kind:string;state:string};
export type EvidenceMetric={label:string;value:string;unit:string};
export type EngineFinding={engine:string;reason:string};
const record=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null&&!Array.isArray(v);
const engines=['orchestrator','runtime','event_store','model','gateway','tools','verifier','finance'] as const;
const count=(v:unknown)=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0?String(v):'—';
export function diagnosticFindings(key:string,phase:string,data:unknown):EngineFinding[]{
 if(key!=='mvp'||phase!=='historical'||!record(data)||!record(data.sections))return [];
 const sections=data.sections;
 if(Object.keys(sections).length!==engines.length||!engines.every(k=>Object.hasOwn(sections,k)&&typeof sections[k]==='string'&&/^[A-Z][A-Z0-9_]{0,127}$/.test(sections[k] as string)))return [];
 return engines.map(engine=>({engine,reason:sections[engine] as string}));
}
export function historicalEvents(key:string,phase:string,data:unknown):EvidenceEvent[]{
 if(phase!=='historical')return [];
 const parsed=key==='lifecycle'?parseLifecycleProjection(data):key==='lifecycle-prefix'?parseLifecyclePrefix(data):null;
 return parsed?parsed.timeline.map(({version,kind,state})=>({version,kind,state})):[];
}
export function historicalMetrics(key:string,phase:string,data:unknown):EvidenceMetric[]{
 if(phase!=='historical'||!record(data))return [];
 if(key==='mvp'&&diagnosticFindings(key,phase,data).length===8)return [
  {label:'Örnek olay satırı',value:count(data.sample_event_rows),unit:'kayıt'},
  {label:'Tanısal kapasite',value:count(data.diagnostic_remaining_minor),unit:'minor'}];
 const parsed=key==='lifecycle'?parseLifecycleProjection(data):key==='lifecycle-prefix'?parseLifecyclePrefix(data):null;
 if(!parsed)return [];
 const common=[{label:'Kayıt revizyonu',value:count(parsed.head_version),unit:'sıra'}, {label:'Örnek muhasebeleşen',value:count(parsed.sample_recognized_minor),unit:parsed.currency+' minor'}];
 return 'sample_released_minor' in parsed?[...common,{label:'Örnek serbest bırakılan',value:count(parsed.sample_released_minor),unit:parsed.currency+' minor'}]:[...common,{label:'Örnek bekleyen rezervasyon',value:count(parsed.sample_outstanding_minor),unit:parsed.currency+' minor'}];
}
/** No timestamps or event sequence can be inferred from a single outbox phase. */
export function outboxEvidence(key:string,phase:string,data:unknown):{phase:string;generation:string;readback:string}|null{
 if(key!=='outbox'||phase!=='historical'||!record(data))return null;
 const p=data.phase,g=data.generation,r=data.readback_recorded;
 if(p!=='LOCAL_HOLD'&&p!=='CLAIMED'&&p!=='UNKNOWN_HOLD'&&p!=='READBACK_HOLD')return null;
 if((p==='LOCAL_HOLD'?g!==null:typeof g!=='number'||!Number.isSafeInteger(g)||g<1)||r!==(p==='READBACK_HOLD'))return null;
 return {phase:p,generation:count(g),readback:r?'Var':'Yok'};
}
