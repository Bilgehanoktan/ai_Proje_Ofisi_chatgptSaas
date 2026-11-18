/** Browser-only D0 read transport. No authority, persistence, retry or live adapter. */
export const endpointCaps = Object.freeze({mvp:16384,admission:4096,outbox:4096,'office-workbench':4096,'task-budget':8192,lifecycle:8192,'lifecycle-prefix':8192,plan:16384} as const);
export type ProjectionKey=keyof typeof endpointCaps;
export type ReadState<T>={phase:'idle'|'loading';data:null}|{phase:'historical';data:T}|{phase:'hold';data:null;reason:'TIMEOUT'|'READBACK_HOLD'};
export type Parser<T>=(raw:unknown)=>T|null;
export async function readProjection<T>(key:ProjectionKey,parse:Parser<T>,signal:AbortSignal,transport:typeof fetch=fetch):Promise<T>{
 if(!Object.hasOwn(endpointCaps,key)||signal.aborted)throw Error('D0_READBACK_HOLD');
 const response=await transport('/api/demo/'+key,{method:'GET',cache:'no-store',redirect:'error',credentials:'same-origin',headers:{Accept:'application/json'},signal});
 if(signal.aborted||!response.ok||response.redirected||response.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json'||!response.body)throw Error('D0_READBACK_HOLD');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(signal.aborted)throw Error('D0_READBACK_HOLD');if(done)break;size+=value.byteLength;if(size>endpointCaps[key])throw Error('D0_READBACK_HOLD');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}
 finally{void reader.cancel().catch(()=>{});reader.releaseLock();}
 const result=parse(JSON.parse(text));if(result===null||signal.aborted)throw Error('D0_READBACK_HOLD');return result;
}
/** One reader per mounted consumer; independent snapshots are never joined implicitly. */
export function createProjectionReader<T>(key:ProjectionKey,parse:Parser<T>,publish:(s:ReadState<T>)=>void,transport:typeof fetch=fetch,timeoutMs=4000){
 let generation=0,active:AbortController|null=null,timer:ReturnType<typeof setTimeout>|undefined;
 function cancel(){generation++;if(timer!==undefined)clearTimeout(timer);timer=undefined;active?.abort();active=null;}
 async function read(){
  cancel();const id=generation,c=new AbortController();active=c;publish({phase:'loading',data:null});
  timer=setTimeout(()=>{if(id!==generation)return;cancel();publish({phase:'hold',data:null,reason:'TIMEOUT'});},timeoutMs);
  try{const data=await readProjection(key,parse,c.signal,transport);if(id===generation&&!c.signal.aborted)publish({phase:'historical',data});}
  catch{if(id===generation&&!c.signal.aborted)publish({phase:'hold',data:null,reason:'READBACK_HOLD'});}
  finally{if(id===generation){if(timer!==undefined)clearTimeout(timer);timer=undefined;active=null;}}
 }
 return {read,cancel};
}
export function readStatus<T>(state:ReadState<T>,labels:{idle:string;loading:string;historical:string;hold:string}):string{return state.phase==='hold'&&state.reason==='TIMEOUT'?'Okuma zaman aşımı · HOLD':labels[state.phase];}
