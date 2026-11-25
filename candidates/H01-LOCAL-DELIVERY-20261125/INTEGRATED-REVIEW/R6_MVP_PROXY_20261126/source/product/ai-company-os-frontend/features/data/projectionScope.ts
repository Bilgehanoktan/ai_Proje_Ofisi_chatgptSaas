import {parseLifecyclePrefix} from '../mvp/lifecyclePrefix';

type Reason='REFERENCE_SHAPE_HOLD'|'SCOPE_MISMATCH'|'REVISION_MISMATCH'|'TASK_MISSING'|'STRUCTURAL_MATCH_ONLY';
export type BindingReview={reason:Reason;join:'HOLD';placement_allowed:false;dispatch_allowed:false};
const review=(reason:Reason):BindingReview=>({reason,join:'HOLD',placement_allowed:false,dispatch_allowed:false});
const record=(x:unknown):x is Record<string,unknown>=>!!x&&typeof x==='object'&&!Array.isArray(x);
/** A display comparison, never a canonical association or authority. */
export function inspectPlanBinding(raw:unknown,plan:unknown):BindingReview{
 const run=parseLifecyclePrefix(raw);
 if(!run||!record(plan)||!record(plan.scope)||!Array.isArray(plan.tasks)||plan.tasks.length<1||plan.tasks.length>100||typeof plan.revision!=='string'||typeof plan.digest!=='string'||!(/^[0-9a-f]{64}$/).test(plan.digest)||plan.revision!=='sha256:'+plan.digest)return review('REFERENCE_SHAPE_HOLD');
 if(plan.scope.tenant_id!==run.tenant||plan.scope.environment_id!==run.environment)return review('SCOPE_MISMATCH');
 if(plan.revision!==run.plan_revision)return review('REVISION_MISMATCH');
 const ids=new Set<string>();
 for(const task of plan.tasks){if(!record(task)||typeof task.id!=='string'||!(/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$/).test(task.id)||ids.has(task.id))return review('REFERENCE_SHAPE_HOLD');ids.add(task.id);}
 if(!ids.has(run.task_id))return review('TASK_MISSING');
 // Plan projection does not prove company, principal, canonical run, clock, placement or causal binding.
 return review('STRUCTURAL_MATCH_ONLY');
}
