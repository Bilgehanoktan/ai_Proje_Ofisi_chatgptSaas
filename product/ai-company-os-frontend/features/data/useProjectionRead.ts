"use client";
import {useEffect,useMemo,useState} from 'react';
import {registeredReader,type ProjectionValue} from './projectionRegistry';
import {type ProjectionKey,type ReadState} from './projectionRead';
export function useProjectionRead<K extends ProjectionKey>(key:K){
 type Data=ProjectionValue<K>;
 const [entry,setEntry]=useState<{key:K;state:ReadState<Data>}>({key,state:{phase:'idle',data:null}});
 const reader=useMemo(()=>registeredReader(key,state=>setEntry({key,state})),[key]);
 useEffect(()=>()=>reader.cancel(),[reader]);
 const state:ReadState<Data>=entry.key===key?entry.state:{phase:'idle',data:null};
 return {state,data:state.data,read:reader.read};
}
