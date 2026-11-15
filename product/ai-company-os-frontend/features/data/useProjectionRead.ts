"use client";
import {useEffect,useMemo,useState} from 'react';
import {createProjectionReader,type ProjectionKey,type ReadState,type Parser} from './projectionRead';
// Key and parser are fixed module-level bindings per consumer. No shared cross-scope cache.
export function useProjectionRead<T>(key:ProjectionKey,parse:Parser<T>){
 const [entry,setEntry]=useState<{key:ProjectionKey;parser:Parser<T>;state:ReadState<T>}>({key,parser:parse,state:{phase:'idle',data:null}});
 const reader=useMemo(()=>createProjectionReader(key,parse,state=>setEntry({key,parser:parse,state})),[key,parse]);
 useEffect(()=>()=>reader.cancel(),[reader]);
 const state:ReadState<T>=entry.key===key&&entry.parser===parse?entry.state:{phase:'idle',data:null};
 return {state,data:state.data,read:reader.read};
}
