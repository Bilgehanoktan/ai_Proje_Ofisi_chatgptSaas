"use client";
import {createContext,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import {parseSharedReplay,readSharedText,type SharedSnapshot} from './sharedSnapshot';
type State={phase:'idle'|'loading'|'hold';data:null}|{phase:'historical';data:SharedSnapshot};
const Shared=createContext<{state:State;read:()=>void}|null>(null);
export function SharedSnapshotProvider({children}:{children:ReactNode}){
 const [state,setState]=useState<State>({phase:'idle',data:null});
 const generation=useRef(0),active=useRef<AbortController|null>(null),expiry=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
 function cancel(){generation.current++;active.current?.abort();active.current=null;clearTimeout(expiry.current);}
 function hold(){cancel();setState({phase:'hold',data:null});}
 useEffect(()=>{const hidden=()=>{if(document.hidden)hold();};document.addEventListener('visibilitychange',hidden);return()=>{document.removeEventListener('visibilitychange',hidden);cancel();};},[]);
 async function read(){
  cancel();const id=generation.current,c=new AbortController();active.current=c;setState({phase:'loading',data:null});
  const timeout=setTimeout(()=>{if(id===generation.current)hold();},4000);
  try{
   const r=await fetch('/api/demo/shared-snapshot',{method:'GET',cache:'no-store',credentials:'same-origin',redirect:'error',headers:{Accept:'text/event-stream'},signal:c.signal});
   const data=await parseSharedReplay(await readSharedText(r,c.signal));
   if(id!==generation.current||c.signal.aborted)return;
   if(document.hidden){hold();return;}
   setState({phase:'historical',data});expiry.current=setTimeout(()=>{if(id===generation.current)hold();},30000);
  }catch{if(id===generation.current)hold();}
  finally{clearTimeout(timeout);if(id===generation.current)active.current=null;}
 }
 return <Shared.Provider value={{state,read}}>{children}</Shared.Provider>;
}
export function useSharedSnapshot(){const context=useContext(Shared);if(!context)throw Error('D0_SHARED_PROVIDER_REQUIRED');return context;}
