/** Exact read-only D0 wire envelope; structural checks never confer authority. */
const sectionKeys = ['orchestrator','runtime','event_store','model','gateway','tools','verifier','finance'] as const;
const rootKeys = ['schema_version','mode','plan_digest','admission','dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted','real_run_count','sections','sample_event_rows','diagnostic_remaining_minor','actual_cost_minor','revenue_minor'];
const record = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const exact = (v: Record<string, unknown>, keys: readonly string[]) => Object.keys(v).length === keys.length && keys.every(k=>Object.hasOwn(v,k));
const sampleNumber = (v: unknown, max: number): v is number|null => v === null || (typeof v === 'number' && Number.isSafeInteger(v) && v >= 0 && v <= max);
export type DiagnosticSection = typeof sectionKeys[number];
export type MvpDiagnostics = {plan_digest:string;sections:Record<DiagnosticSection,string>;sample_event_rows:number|null;diagnostic_remaining_minor:number|null};
export function parseMvpDiagnostics(v: unknown): MvpDiagnostics|null {
 if(!record(v)||!exact(v,rootKeys)||v.schema_version!=='mvp.diagnostics.v1-D0'||v.mode!=='SYNTHETIC_LOCAL_ONLY'||v.admission!=='DENY'||typeof v.plan_digest!=='string'||!/^[a-f0-9]{64}$/.test(v.plan_digest))return null;
 if(['dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted'].some(k=>v[k]!==false)||['real_run_count','actual_cost_minor','revenue_minor'].some(k=>v[k]!==null))return null;
 if(!record(v.sections)||!exact(v.sections,sectionKeys)||!sampleNumber(v.sample_event_rows,100)||!sampleNumber(v.diagnostic_remaining_minor,Number.MAX_SAFE_INTEGER))return null;
 const sections={} as Record<DiagnosticSection,string>;
 for(const key of sectionKeys){const s=v.sections[key];if(typeof s!=='string'||!/^[A-Z][A-Z0-9_]{0,127}$/.test(s))return null;sections[key]=s;}
 return {plan_digest:v.plan_digest,sections,sample_event_rows:v.sample_event_rows,diagnostic_remaining_minor:v.diagnostic_remaining_minor};
}
