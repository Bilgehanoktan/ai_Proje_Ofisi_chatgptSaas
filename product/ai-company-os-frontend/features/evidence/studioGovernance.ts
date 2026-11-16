/** D0 presentation only: no staffing, grant, install or execution. */
export type RoleTemplate={id:string;name:string;department:string;description:string};
const expected=['orchestrator','research','engineer','qa'] as const;
export function organizationTemplate(roles:readonly RoleTemplate[]){
 const ids=roles.map(r=>r.id);
 if(ids.length!==expected.length||new Set(ids).size!==ids.length||!expected.every(id=>ids.includes(id))||roles.some(r=>!r.name.trim()||!r.department.trim()))return null;
 const groups=[...new Set(roles.map(r=>r.department))].sort().map(department=>({department,roles:roles.filter(r=>r.department===department)}));
 return {human:'H01',coordinator:roles.find(r=>r.id==='orchestrator')!,groups,independent:['Independent Verifier','Policy / PEP','W-A witness'] as const,actualEmployees:null,assignmentAllowed:false,decision:'HOLD'} as const;
}
export const skillStages=[{id:'source',label:'Kaynak ve provenance',status:'HOLD'},{id:'quarantine',label:'Karantina ve manifest',status:'QUARANTINED'},{id:'review',label:'F0 / bağımsız makbuz',status:'HOLD'},{id:'publish',label:'Yayın ve etkinleştirme',status:'DENY'}] as const;
export function skillBoundary(){return {stages:skillStages,installedCount:null,enabledCount:null,effectiveTools:[],installAllowed:false,grantAllowed:false,executionAllowed:false,decision:'HOLD'} as const;}
