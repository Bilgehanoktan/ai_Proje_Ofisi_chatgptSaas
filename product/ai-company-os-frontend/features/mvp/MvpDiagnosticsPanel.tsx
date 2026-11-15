"use client";
import {useRef,useState,useEffect} from 'react';
import {parseMvpDiagnostics,type MvpDiagnostics} from './mvpDiagnostics';
export default function MvpDiagnosticsPanel(){
 const [data,setData]=useState<MvpDiagnostics|null>(null),[state,setState]=useState('Henüz okunmadı · HOLD');
 const pending=useRef<AbortController|null>(null);
 useEffect(()=>()=>pending.current?.abort(),[]);
 async function read(){
  pending.current?.abort();const controller=new AbortController();pending.current=controller;setData(null);setState('Yerel sentetik tanılama okunuyor…');
  try{const r=await fetch('/api/demo/mvp',{cache:'no-store',signal:controller.signal,redirect:'error'});const body=r.ok?parseMvpDiagnostics(await r.json()):null;if(controller.signal.aborted)return;if(!body)throw Error('contract');setData(body);setState('Sentetik backend okuması · DENY / HOLD');}
  catch{if(!controller.signal.aborted)setState('Backend erişilemiyor veya sözleşme uyumsuz · HOLD');}
 }
 return <section className="panel" aria-label="Yerel MVP tanılama"><div className="bar"><div><h2>Yerel MVP tanılama</h2><p className="sub">Salt okunur · gerçek ajan, finans veya yetki yok</p></div><button type="button" onClick={read}>Sentetik backend oku</button></div><p role="status">{state}</p>{data&&<><p>Plan: {data.plan_digest.slice(0,12)}…</p><dl>{Object.entries(data.sections).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><p>SQLite örnek satır: {data.sample_event_rows??'—'} · Sentetik kalan kapasite (minor): {data.diagnostic_remaining_minor??'—'}</p></>}</section>;
}
