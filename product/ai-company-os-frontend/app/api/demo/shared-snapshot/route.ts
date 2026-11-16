import {localBackendPort} from '../../../../features/mvp/localBackend';
import {parseSharedReplay,readSharedText} from '../../../../features/data/sharedSnapshot';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function GET(request:Request){
 try{
  if(request.headers.has('last-event-id'))throw Error('full resync required');
  const signal=AbortSignal.timeout(2500);
  const r=await fetch('http://127.0.0.1:'+localBackendPort()+'/demo/v1/lifecycle/shared-snapshot',{method:'GET',cache:'no-store',redirect:'error',signal,headers:{Accept:'text/event-stream'}});
  const body=await readSharedText(r,signal);await parseSharedReplay(body);
  if(signal.aborted)throw Error('timeout');
  return new Response(body,{headers:{...headers,'Content-Type':'text/event-stream; charset=utf-8'}});
 }catch{return Response.json({mode:'D0_SHARED_SNAPSHOT_HOLD'},{status:503,headers});}
}
