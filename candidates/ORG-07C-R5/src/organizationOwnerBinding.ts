/** ORG-07C-R5: consumer-side historical projection binding. Not IAM or a route. */
import {readOrganizationProxy} from '../original/organizationProxy';
import {parseOrganization, type OrganizationProjection} from '../original/organizationProjection';
type Scope=OrganizationProjection['scope'];
export type OwnerReadBinding=Readonly<{credential:string;scope:Readonly<Scope>;revision:string}>;
// Only a future trusted server composition may supply this port. No implementation here.
export type OwnerReadProvider=(request:Request,signal:AbortSignal)=>Promise<OwnerReadBinding|null>;
const headers={'Cache-Control':'no-store','Pragma':'no-cache','Vary':'Cookie, Authorization'};
const hold=()=>Response.json({mode:'D0_ORGANIZATION_READ_HOLD'},{status:503,headers});
const synthetic=(s:unknown):s is string=>typeof s==='string'&&s.length<=128&&/^synthetic-[A-Za-z0-9_.:-]+$/.test(s);
const digest=(s:unknown):s is string=>typeof s==='string'&&/^[0-9a-f]{64}$/.test(s);
function exact(value:unknown,keys:readonly string[]):value is Record<string,unknown>{
 return value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
}
function snapshot(raw:unknown):OwnerReadBinding|null{
 if(!exact(raw,['credential','scope','revision'])||typeof raw.credential!=='string'||!digest(raw.revision))return null;
 const s=raw.scope;
 if(!exact(s,['tenant_id','company_id','environment_id'])||!synthetic(s.tenant_id)||!synthetic(s.company_id)||(s.environment_id!=='A0_SAMPLE_ONLY'&&s.environment_id!=='A0_REVIEW_ONLY'))return null;
 return Object.freeze({credential:raw.credential,scope:Object.freeze({tenant_id:s.tenant_id,company_id:s.company_id,environment_id:s.environment_id}),revision:raw.revision});
}
export async function readOwnerBoundOrganization(request:Request,port:number,owner?:OwnerReadProvider,transport:typeof fetch=fetch):Promise<Response>{
 if(!owner)return hold();
 try{
  // Keep the existing proxy responsible for request validation, credential syntax, timeout and fetch.
  const state:{binding?:Readonly<{scope:Readonly<Scope>;revision:string}>;signal?:AbortSignal;called:boolean}={called:false};
  const response=await readOrganizationProxy(request,port,async(req,signal)=>{
   if(state.called||signal.aborted)return null;
   state.called=true;state.signal=signal;
   const value=snapshot(await owner(req,signal));
   if(!value||signal.aborted)return null;
   state.binding=Object.freeze({scope:value.scope,revision:value.revision});
   return value.credential;
  },transport);
  if(response.status!==200||!state.binding||!state.signal||state.signal.aborted||request.signal.aborted)return hold();
  const projection=parseOrganization(await response.json());
  const b=state.binding;
  if(!projection||state.signal.aborted||request.signal.aborted||projection.revision!==b.revision||projection.scope.tenant_id!==b.scope.tenant_id||projection.scope.company_id!==b.scope.company_id||projection.scope.environment_id!==b.scope.environment_id)return hold();
  // Projection remains historical HOLD. No token, identity, grant or owner metadata in response.
  return Response.json(projection,{headers});
 }catch{return hold();}
}
