"use client";
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {createSharedReplaySession,type SharedSessionState} from './sharedReplaySession';
import {useProjectionRead} from './useProjectionRead';
const Shared=createContext<{state:SharedSessionState;read:()=>void;reset:()=>void;planRead:ReturnType<typeof useProjectionRead<'plan'>>;organizationRead:ReturnType<typeof useProjectionRead<'organization'>>}|null>(null);
export function SharedSnapshotProvider({children}:{children:ReactNode}){
 const planRead=useProjectionRead('plan');
 // Independent historical ORG reader shared by presentation surfaces, never an atomic join.
 const organizationRead=useProjectionRead('organization');
 const [state,setState]=useState<SharedSessionState>({phase:'idle',data:null});
 const [session]=useState(()=>createSharedReplaySession({onChange:setState,isHidden:()=>document.hidden,request:signal=>fetch('/api/demo/shared-snapshot',{method:'GET',cache:'no-store',credentials:'same-origin',redirect:'error',headers:{Accept:'text/event-stream'},signal})}));
 useEffect(()=>{const hidden=()=>{if(document.hidden)session.invalidate();};document.addEventListener('visibilitychange',hidden);return()=>{document.removeEventListener('visibilitychange',hidden);session.cancel();};},[session]);
 return <Shared.Provider value={{state,read:session.read,reset:session.reset,planRead,organizationRead}}>{children}</Shared.Provider>;
}
export function useSharedSnapshot(){const context=useContext(Shared);if(!context)throw Error('D0_SHARED_PROVIDER_REQUIRED');return context;}
