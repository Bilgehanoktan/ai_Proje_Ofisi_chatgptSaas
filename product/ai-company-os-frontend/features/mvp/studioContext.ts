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
