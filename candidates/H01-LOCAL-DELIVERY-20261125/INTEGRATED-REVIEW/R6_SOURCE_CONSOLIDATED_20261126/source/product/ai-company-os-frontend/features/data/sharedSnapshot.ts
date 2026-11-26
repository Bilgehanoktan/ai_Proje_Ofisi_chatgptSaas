/** Bounded finite SSE replay; no EventSource, live cursor, placement or authority. */
import {parseLifecyclePrefix,type LifecyclePrefix} from '../mvp/lifecyclePrefix';
export const sharedCap=16384;
export const sharedProfile='ceo-office.prefix.v1-D0' as const;
export type SharedSnapshot={profile:typeof sharedProfile;source:'D0_0196L_HISTORICAL_PREFIX';project_id:null;world_id:null;snapshot_seq:number;prefix:LifecyclePrefix;digest:string};
function canonical(value:unknown):string{
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 if(value!==null&&typeof value==='object'){const r=value as Record<string,unknown>;return '{'+Object.keys(r).sort().map(k=>JSON.stringify(k)+':'+canonical(r[k])).join(',')+'}';}
 return JSON.stringify(value);
}
const same=(a:unknown,b:unknown)=>canonical(a)===canonical(b);
export async function parseSharedReplay(text:string):Promise<SharedSnapshot>{
 if(!text.endsWith('\n\n')||text.length>sharedCap||/[^\x20-\x7e\n]/.test(text))throw Error('D0_SHARED_FRAME_HOLD');
 const frames=text.slice(0,-2).split('\n\n');
 if(frames.length<3||frames.length>6)throw Error('D0_SHARED_COUNT_HOLD');
 function frame(i:number,kind:string):unknown{
  const lines=frames[i].split('\n');
  if(lines.length!==2||lines[0]!=='event: '+kind||!lines[1].startsWith('data: '))throw Error('D0_SHARED_ORDER_HOLD');
  const raw=lines[1].slice(6),data:unknown=JSON.parse(raw);
  if(canonical(data)!==raw)throw Error('D0_SHARED_CANONICAL_HOLD');
  return data;
 }
 const raw=frame(0,'snapshot');
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('D0_SHARED_SNAPSHOT_HOLD');
 const row=raw as Record<string,unknown>,prefix=parseLifecyclePrefix(row.prefix);
 if(!prefix)throw Error('D0_SHARED_PREFIX_HOLD');
 const body={profile:sharedProfile,source:'D0_0196L_HISTORICAL_PREFIX' as const,project_id:null,world_id:null,snapshot_seq:prefix.head_version,prefix};
 const bytes=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(body)));
 const digest=Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
 const snapshot={...body,digest};
 if(!same(raw,snapshot)||frames.length!==prefix.head_version+2)throw Error('D0_SHARED_SCOPE_HOLD');
 for(let i=1;i<=prefix.head_version;i++)if(!same(frame(i,'history'),{digest,sequence:i,entry:prefix.timeline[i-1]}))throw Error('D0_SHARED_SEQUENCE_HOLD');
 if(!same(frame(frames.length-1,'complete'),{digest,sequence:prefix.head_version}))throw Error('D0_SHARED_COMPLETE_HOLD');
 return snapshot;
}
export async function readSharedText(response:Response,signal:AbortSignal):Promise<string>{
 if(signal.aborted||!response.ok||response.redirected||response.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='text/event-stream'||!response.body)throw Error('D0_SHARED_RESPONSE_HOLD');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let size=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(signal.aborted)throw Error('D0_SHARED_ABORT');if(done)break;size+=value.byteLength;if(size>sharedCap)throw Error('D0_SHARED_SIZE_HOLD');text+=decoder.decode(value,{stream:true});}return text+decoder.decode();}
 finally{void reader.cancel().catch(()=>{});reader.releaseLock();}
}
