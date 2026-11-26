/** U2 shared historical session: one in-memory reader, no runtime authority. */
import {parseSharedReplay,readSharedText,type SharedSnapshot} from './sharedSnapshot';
import {beforeDeadline} from '../mvp/readBoundedD0Json';
export const SHARED_READ_TIMEOUT_MS=4000;
export const SHARED_DISPLAY_TTL_MS=30000;
export type SharedSessionState=Readonly<{phase:'idle'|'loading'|'hold';data:null}>|Readonly<{phase:'historical';data:SharedSnapshot}>;
type Cancel=()=>void;
export type SharedSessionOptions=Readonly<{request:(signal:AbortSignal)=>Promise<Response>;onChange:(state:SharedSessionState)=>void;isHidden:()=>boolean;schedule?:(callback:()=>void,ms:number)=>Cancel}>;
const idle=():SharedSessionState=>Object.freeze({phase:'idle',data:null});
function freeze<T>(value:T):T{if(value&&typeof value==='object'&&!Object.isFrozen(value)){for(const item of Object.values(value))freeze(item);Object.freeze(value);}return value;}
export function createSharedReplaySession(options:SharedSessionOptions){
 const {request,onChange,isHidden}=options;
 const schedule=options.schedule??((callback,ms)=>{const timer=setTimeout(callback,ms);return ()=>clearTimeout(timer);});
 let state=idle(),generation=0,active:AbortController|null=null,readTimer:Cancel|null=null,expiry:Cancel|null=null;
 const snapshot=()=>state;
 const publish=(next:SharedSessionState)=>{state=Object.freeze(next);onChange(state);};
 function cancel(){generation++;active?.abort();active=null;readTimer?.();readTimer=null;expiry?.();expiry=null;}
 function reset(){cancel();publish(idle());}
 function invalidate(){cancel();publish({phase:'hold',data:null});}
 async function read(){
  cancel();if(isHidden()){invalidate();return;}
  const id=generation,controller=new AbortController();active=controller;
  publish({phase:'loading',data:null});
  if(id!==generation)return;
  readTimer=schedule(()=>{if(id===generation)invalidate();},SHARED_READ_TIMEOUT_MS);
  try{
   const response=await beforeDeadline(request(controller.signal),controller.signal);
   if(id!==generation||controller.signal.aborted)return;
   const data=await beforeDeadline(parseSharedReplay(await readSharedText(response,controller.signal)),controller.signal);
   if(id!==generation||controller.signal.aborted)return;
   if(isHidden()){invalidate();return;}
   readTimer?.();readTimer=null;active=null;
   expiry=schedule(()=>{if(id===generation)invalidate();},SHARED_DISPLAY_TTL_MS);
   publish({phase:'historical',data:freeze(data)});
  }catch{if(id===generation)invalidate();}
 }
 return Object.freeze({snapshot,read,reset,invalidate,cancel});
}
