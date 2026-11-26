/** D0 offline projection guard. No scheduling, network, signature or grant validation. */
import sample from '../../fixtures/core.preview.json';
import projection from '../../fixtures/core.plan.projection.json';
export type PlanTask = typeof projection.tasks[number];
const PIN = "6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9";
export function readPlanProjection(p: typeof projection = projection): {ok:true; plan:typeof projection; groups:PlanTask[][]}|{ok:false; reason:string} {
  const hold = (reason:string) => ({ok:false as const,reason});
  if (p.schema_version !== 'core.plan.projection.v1-D0' || p.scope.tenant_id !== 'synthetic-tenant' || p.scope.environment_id !== 'A0_SAMPLE_ONLY' || p.plan_id !== sample.plan.id || p.worktype !== sample.plan.worktype || p.validation !== 'VALIDATED_D0_GRAPH' || p.digest !== PIN || p.revision !== 'sha256:'+PIN || p.admission !== 'DENY' || p.dispatch_allowed !== false || p.release_ready !== false || p.real_run_count !== null) return hold('PLAN_SCOPE_OR_PIN_MISMATCH');
  const byId = new Map(p.tasks.map(t=>[t.id,t]));
  if (!p.tasks.length || byId.size !== p.tasks.length || p.tasks.length !== sample.plan.tasks.length) return hold('TASK_SET_MISMATCH');
  const same = (a:string[],b:string[]) => a.length===b.length && a.every((v,i)=>v===b[i]);
  for (const source of sample.plan.tasks) {
    const t=byId.get(source.id);
    if (!t || t.label!==source.label || t.role!==source.role || t.state!=='HOLD' || t.run_id!==null || !same(t.depends_on,[...source.depends_on].sort())) return hold('TASK_BINDING_MISMATCH');
  }
  if (!same(p.tasks.map(t=>t.id),[...byId.keys()].sort())) return hold('TASK_ORDER_MISMATCH');
  const expectedEdges=p.tasks.flatMap(t=>t.depends_on.map(d=>JSON.stringify([d,t.id])));
  if (!same(p.edges.map(e=>JSON.stringify([e.from,e.to])),expectedEdges)) return hold('EDGE_MISMATCH');
  const levels=new Map<string,number>();
  const groups:PlanTask[][]=[];
  for (const [level,wave] of p.waves.entries()) {
    if (!wave.length || !same(wave,[...wave].sort())) return hold('WAVE_ORDER_INVALID');
    const group:PlanTask[]=[];
    for (const id of wave) {
      const t=byId.get(id);
      if (!t || levels.has(id) || t.depends_on.some(d=>!levels.has(d) || levels.get(d)!>=level)) return hold('WAVE_DEPENDENCY_INVALID');
      const expected=t.depends_on.length?Math.max(...t.depends_on.map(d=>levels.get(d)!))+1:0;
      if (expected!==level) return hold('WAVE_LEVEL_INVALID');
      levels.set(id,level); group.push(t);
    }
    groups.push(group);
  }
  if (levels.size!==byId.size) return hold('WAVE_COVERAGE_INVALID');
  return {ok:true,plan:p,groups};
}
