/** ORG-07C: server-only proxy seam. A real session owner is NOT supplied here. */
import {organizationCap,parseOrganization} from './organizationProjection';
export type CredentialProvider=(request:Request,signal:AbortSignal)=>Promise<string|null>;
const headers={'Cache-Control':'no-store','Pragma':'no-cache','Vary':'Cookie, Authorization'};
const hold=()=>Response.json({mode:'D0_ORGANIZATION_READ_HOLD'},{status:503,headers});
function bounded<T>(work:()=>Promise<T>,signal:AbortSignal):Promise<T>{
 return new Promise((resolve,reject)=>{
  if(signal.aborted){reject(Error('aborted'));return;}
  const stop=()=>{cleanup();reject(Error('aborted'));};
  const cleanup=()=>signal.removeEventListener('abort',stop);
  signal.addEventListener('abort',stop,{once:true});
  Promise.resolve().then(work).then(v=>{cleanup();resolve(v);},e=>{cleanup();reject(e);});
 });
}
export async function readOrganizationProxy(request:Request,port:number,credential?:CredentialProvider,transport:typeof fetch=fetch):Promise<Response>{
 try{
  if(request.method!=='GET'||new URL(request.url).search||request.body!==null||request.headers.has('authorization')||request.signal.aborted||!credential||!Number.isInteger(port)||port<1024||port>49151)return hold();
  const signal=AbortSignal.any([request.signal,AbortSignal.timeout(2500)]);
  const token=await bounded(()=>credential(request,signal),signal);
  if(typeof token!=='string'||token.length>4096||!/^[A-Za-z0-9._~+/-]{1,4096}={0,2}$/.test(token)||signal.aborted)return hold();
  const r=await transport(`http://127.0.0.1:${port}/demo/v1/organization/studio-preview`,{method:'GET',cache:'no-store',redirect:'error',signal,headers:{Accept:'application/json',Authorization:'Bearer '+token}});
  if(!r.ok||r.redirected||r.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json'||!r.body)return hold();
  const stream=r.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
  try{for(;;){const {done,value}=await stream.read();if(signal.aborted)throw Error('aborted');if(done)break;size+=value.byteLength;if(size>organizationCap)throw Error('cap');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}
  finally{await stream.cancel().catch(()=>{});stream.releaseLock();}
  const parsed=parseOrganization(JSON.parse(text));if(!parsed||signal.aborted)return hold();
  return Response.json(parsed,{headers});
 }catch{return hold();}
}
