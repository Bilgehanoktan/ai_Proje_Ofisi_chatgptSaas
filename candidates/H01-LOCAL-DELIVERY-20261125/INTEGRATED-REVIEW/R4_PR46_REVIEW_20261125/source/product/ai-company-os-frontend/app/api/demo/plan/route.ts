import {localBackendPort} from '../../../../features/mvp/localBackend';
import {parsePlanProjection} from '../../../../features/core-review/planProjection';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function GET(){
 try{
  const signal=AbortSignal.timeout(2500);
  const r=await fetch('http://127.0.0.1:'+localBackendPort()+'/demo/v1/core/plan-projection',{method:'GET',cache:'no-store',redirect:'error',signal,headers:{Accept:'application/json'}});
  if(signal.aborted||!r.ok||r.redirected||r.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json'||!r.body)throw Error('D0_PLAN_RESPONSE_HOLD');
  const reader=r.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
  try{for(;;){const {done,value}=await reader.read();if(signal.aborted)throw Error('timeout');if(done)break;size+=value.byteLength;if(size>16384)throw Error('size');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}
  finally{void reader.cancel().catch(()=>{});reader.releaseLock();}
  const plan=parsePlanProjection(JSON.parse(text));
  if(!plan||signal.aborted)throw Error('D0_PLAN_CONTRACT_HOLD');
  return Response.json(plan,{headers});
 }catch{return Response.json({mode:'D0_PLAN_READBACK_HOLD'},{status:503,headers});}
}
