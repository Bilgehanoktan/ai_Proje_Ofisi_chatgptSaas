/** Plan-role context only; never an agent assignment or a join with historical samples. */
export type PlanRoleTask={id:string;label:string;role:string;state:string;depends_on:readonly string[]};
export function studioContext(task:PlanRoleTask|undefined){
 if(!task||!task.id||!task.label||!task.role||task.state!=='HOLD'||!Array.isArray(task.depends_on))return null;
 return {taskId:task.id,taskLabel:task.label,roleLabel:task.role,dependencyCount:task.depends_on.length,
  roleStatus:'PLAN_ROLE_ONLY',agentLabel:'Atanmış ajan doğrulanmadı',runLabel:'Run bilinmiyor',
  decision:'HOLD',dispatchAllowed:false,placementAllowed:false} as const;
}
/** A historical sample never establishes a current agent or placement. */
export function historicalAgentContext(){
 return {agentLabel:'Güncel ajan doğrulanmadı',runLabel:'Canlı run bilinmiyor',decision:'HOLD',
  dispatchAllowed:false,placementAllowed:false} as const;
}

import {inspectHistoricalJoin,type PlanIdentity} from './historicalJoin';
import {parseLifecyclePrefix} from './lifecyclePrefix';
import type {SharedSnapshot} from '../data/sharedSnapshot';
export type StudioSelection={kind:'task'|'role';id:string};
export function rolePlanTasks<T extends PlanRoleTask>(tasks:readonly T[],roleId:string):T[]{
 return tasks.filter(t=>t.role===roleId&&studioContext(t)!==null);
}
/** Independent historical evidence, never an assignment to the selected role or node. */
export function reviewStudioEvidence(plan:PlanIdentity|null,selection:StudioSelection,snapshot:SharedSnapshot|null){
 const base={selection,decision:'HOLD',joinAllowed:false,dispatchAllowed:false,placementAllowed:false,assignment:null} as const;
 const p=snapshot&&parseLifecyclePrefix(snapshot.prefix);
 if(!snapshot||!p||snapshot.profile!=='ceo-office.prefix.v1-D0'||snapshot.source!=='D0_0196L_HISTORICAL_PREFIX'||snapshot.project_id!==null||snapshot.world_id!==null||snapshot.snapshot_seq!==p.head_version||!/^[a-f0-9]{64}$/.test(snapshot.digest))
  return {...base,reason:'NO_VERIFIED_SESSION' as const,observation:null};
 const reason=plan?inspectHistoricalJoin(plan,p).reason:'PLAN_UNAVAILABLE' as const;
 return {...base,reason,observation:{scope:[p.tenant,p.company,p.environment] as const,planRevision:p.plan_revision,taskId:p.task_id,runId:p.run_id,agentRef:p.agent_instance_id,principalRef:p.principal_id,state:p.state,sequence:p.head_version,policyEpoch:p.policy_epoch,witnessEpoch:p.witness_epoch,digest:snapshot.digest,timeline:p.timeline,modelBinding:p.model_binding,memoryAcl:p.memory_acl,geometryJoin:p.geometry_join,leaseFreshness:p.lease_freshness}};
}
