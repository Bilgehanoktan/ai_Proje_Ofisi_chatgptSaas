"use client";
import {useEffect,useMemo,useState} from 'react';
import {registeredReader,type ProjectionValue} from './projectionRegistry';
import {type ProjectionKey} from './projectionRead';
import {sessionReadState,type SessionEntry} from './projectionSession';
export function useProjectionRead<K extends ProjectionKey>(key:K){
 type Data=ProjectionValue<K>;
 const [entry,setEntry]=useState<SessionEntry<Data>|null>(null);
 const session=useMemo(()=>{
  const owner={};
  return {owner,reader:registeredReader(key,state=>setEntry({owner,state}))};
 },[key]);
 useEffect(()=>{
  // Invalidate independent historical D0 cards when the tab loses visibility.
  // This is display revocation, not an IAM/session authority check.
  const hidden=()=>{if(document.hidden)session.reader.invalidate();};
  document.addEventListener('visibilitychange',hidden);
  return()=>{document.removeEventListener('visibilitychange',hidden);session.reader.cancel();};
 },[session]);
 const state=sessionReadState(session.owner,entry);
 function reset(){session.reader.cancel();setEntry(null);}
 return {state,data:state.data,read:session.reader.read,reset};
}
