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
 useEffect(()=>()=>session.reader.cancel(),[session]);
 const state=sessionReadState(session.owner,entry);
 return {state,data:state.data,read:session.reader.read};
}
