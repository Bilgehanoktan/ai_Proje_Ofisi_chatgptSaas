import {parseOutboxProjection} from '../../../../features/mvp/outboxProjection';
export const dynamic='force-dynamic';
import {localBackendPort} from '../../../../features/mvp/localBackend';
const headers={'Cache-Control':'no-store'};
export async function GET(){
 try{
  const endpoint=`http://127.0.0.1:${localBackendPort()}/demo/v1/outbox/review-projection`;
  const r=await fetch(endpoint,{method:'GET',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(2500),headers:{Accept:'application/json'}});
  if(!r.ok||!r.headers.get('content-type')?.startsWith('application/json')||!r.body)throw Error('response');
  const reader=r.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
  try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>4096)throw Error('size');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
  const body:unknown=JSON.parse(text);
  if(!parseOutboxProjection(body))throw Error('contract');
  return Response.json(body,{headers});
 }catch{return Response.json({mode:'D0_OUTBOX_READBACK_HOLD'},{status:503,headers});}
}
