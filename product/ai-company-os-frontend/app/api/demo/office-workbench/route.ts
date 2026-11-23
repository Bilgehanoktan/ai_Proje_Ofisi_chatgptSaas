import {parseOfficeWorkbench} from '../../../../features/mvp/officeWorkbenchProjection';
export const dynamic='force-dynamic';
import {localBackendPort} from '../../../../features/mvp/localBackend';
const headers={'Cache-Control':'no-store'};

// An absolute deadline for the entire response pipeline, including uncooperative
// fetch(), ReadableStream.read() and cancel() promises that ignore signal.abort.
async function boundToDeadline<T>(signal:AbortSignal, work:()=>Promise<T>):Promise<T>{
 if(signal.aborted)throw Error('deadline');
 let onAbort=()=>{};
 const deadline=new Promise<never>((_,reject)=>{
  onAbort=()=>reject(Error('deadline'));
  signal.addEventListener('abort',onAbort,{once:true});
  if(signal.aborted)onAbort();
 });
 try{return await Promise.race([work(),deadline]);}
 finally{signal.removeEventListener('abort',onAbort);}
}

async function readOfficeWorkbench(signal:AbortSignal):Promise<Response>{
 const endpoint=`http://127.0.0.1:${localBackendPort()}/demo/v1/office/workbench-projection`;
 if(signal.aborted)throw Error('deadline');
 const r=await fetch(endpoint,{method:'GET',cache:'no-store',redirect:'error',signal,headers:{Accept:'application/json'}});
 if(signal.aborted)throw Error('deadline');
 if(!r.ok||r.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json'||!r.body)throw Error('response');
 const reader=r.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>4096)throw Error('size');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}
 finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
 const body:unknown=JSON.parse(text);if(!parseOfficeWorkbench(body))throw Error('contract');
 if(signal.aborted)throw Error('deadline');
 return Response.json(body,{headers});
}

export async function GET(){
 try{
  const signal=AbortSignal.timeout(2500);
  return await boundToDeadline(signal,()=>readOfficeWorkbench(signal));
 }catch{return Response.json({mode:'D0_OFFICE_WORKBENCH_HOLD'},{status:503,headers});}
}
