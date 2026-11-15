/** Fixed historical prefix profile; no live freshness or authority. */
const steps=[['D0_RUN_ADMISSION','ADMITTED'],['D0_RUN_TRANSITION','RUNNING'],['D0_LEASE_RENEWAL','RUNNING'],['D0_RUN_TRANSITION','VERIFYING']] as const;
const fixed={schema_version:'lifecycle.prefix.v1-D0',mode:'D0_0196L_HISTORICAL_PREFIX',tenant:'synthetic-tenant',company:'synthetic-company',environment:'A0_SAMPLE_ONLY',plan_revision:'sha256:c75ec1070786538f38bdccdcf6a75de62a9e02e9bcb7e4a4bb9df5f7e96638a0',task_id:'a',run_id:'demo-a',agent_instance_id:'demo-agent',principal_id:'demo-principal',attempt:0,lease_present:true,fence:1,policy_epoch:2,witness_epoch:3,sample_outstanding_minor:20,sample_recognized_minor:0,currency:'USD',freshness:'HISTORICAL_SAMPLE',lease_freshness:'UNKNOWN',causality:'EXACT_FIXED_PREFIX_ONLY',geometry_join:'HOLD',model_binding:'HOLD',memory_acl:'HOLD',independent_acceptance:'HOLD',decision:'HOLD',dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,authoritative:false,real_run_count:null} as const;
function expected(v:1|2|3|4){const renewed=v>=3;return {...fixed,head_version:v,state:steps[v-1][1],timeline:steps.slice(0,v).map(([kind,state],i)=>({version:i+1,kind,state})),lease_version:renewed?2:1,heartbeat_revision:renewed?1:0,heartbeat_tick:renewed?11:10,expires_tick:renewed?31:20,sample_budget_revision:renewed?2:1};}
export type LifecyclePrefix=ReturnType<typeof expected>;
function same(a:unknown,b:unknown):boolean{
 if(a===b)return true;
 if(Array.isArray(b))return Array.isArray(a)&&a.length===b.length&&b.every((v,i)=>same(a[i],v));
 if(b!==null&&typeof b==='object'){
  if(a===null||typeof a!=='object'||Array.isArray(a))return false;
  const x=a as Record<string,unknown>,y=b as Record<string,unknown>;
  return Object.keys(x).length===Object.keys(y).length&&Object.keys(y).every(k=>Object.hasOwn(x,k)&&same(x[k],y[k]));
 }
 return false;
}
export function parseLifecyclePrefix(raw:unknown):LifecyclePrefix|null{
 if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
 const v=(raw as Record<string,unknown>).head_version;
 if(v!==1&&v!==2&&v!==3&&v!==4)return null;
 const e=expected(v);return same(raw,e)?e:null;
}
