/** Identity comparison only, never grants a current DAG or Office join. */
export type PlanIdentity={scope:{tenant_id:string;environment_id:string;company_id?:string};revision:string;tasks:readonly {id:string;run_id:string|null}[]};
export type HistoricalIdentity={tenant:string;company:string;environment:string;plan_revision:string;task_id:string;run_id:string;freshness:'HISTORICAL_SAMPLE'};
export type JoinReason='SCOPE_MISMATCH'|'PLAN_REVISION_MISMATCH'|'TASK_MISSING_OR_DUPLICATE'|'COMPANY_SCOPE_MISSING'|'RUN_BINDING_MISSING_OR_MISMATCH'|'HISTORICAL_ONLY';
export function inspectHistoricalJoin(plan:PlanIdentity,sample:HistoricalIdentity):{decision:'HOLD';reason:JoinReason;join_allowed:false}{
 let reason:JoinReason;
 if(plan.scope.tenant_id!==sample.tenant||plan.scope.environment_id!==sample.environment||(plan.scope.company_id!==undefined&&plan.scope.company_id!==sample.company))reason='SCOPE_MISMATCH';
 else if(!/^sha256:[a-f0-9]{64}$/.test(plan.revision)||plan.revision!==sample.plan_revision)reason='PLAN_REVISION_MISMATCH';
 else {const tasks=plan.tasks.filter(t=>t.id===sample.task_id);
  if(tasks.length!==1)reason='TASK_MISSING_OR_DUPLICATE';
  else if(!plan.scope.company_id)reason='COMPANY_SCOPE_MISSING';
  else if(tasks[0].run_id===null||tasks[0].run_id!==sample.run_id)reason='RUN_BINDING_MISSING_OR_MISMATCH';
  else reason='HISTORICAL_ONLY';
 }
 return {decision:'HOLD',reason,join_allowed:false};
}
