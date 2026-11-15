"use client";
import {useRef,useState,useEffect} from 'react';
import {parseOutboxProjection,type OutboxProjection} from './outboxProjection';
export default function OutboxProjectionPanel(){
 const [data,setData]=useState<OutboxProjection|null>(null),[state,setState]=useState('Henüz okunmadı · HOLD');
 const pending=useRef<AbortController|null>(null);
 useEffect(()=>()=>pending.current?.abort(),[]);
 async function read(){
  pending.current?.abort();const controller=new AbortController();pending.current=controller;setData(null);setState('Yerel sentetik Outbox okunuyor…');
  try{const r=await fetch('/api/demo/outbox',{cache:'no-store',signal:controller.signal,redirect:'error'});const body=r.ok?parseOutboxProjection(await r.json()):null;if(controller.signal.aborted)return;if(!body)throw Error('contract');setData(body);setState('Sentetik okuma · DENY');}
  catch{if(!controller.signal.aborted)setState('Yerel örnek yok veya sözleşme uyumsuz · HOLD');}
 }
 return <section className="panel" aria-label="Sentetik Outbox mutabakatı"><div className="bar"><div><h2>Outbox inceleme · D0</h2><p className="sub">Salt okunur örnek · claim gönderim yetkisi değildir</p></div><button type="button" onClick={read}>Outbox oku</button></div><p role="status">{state}</p>{data&&<dl><div><dt>İnceleme durumu</dt><dd>{data.phase}</dd></div><div><dt>İnceleme nesli</dt><dd>{data.generation??'—'}</dd></div><div><dt>Örnek readback kaydı</dt><dd>{data.readback_recorded?'Var · HOLD':'Yok'}</dd></div></dl>}<p>Gönderim / yeniden deneme / yayın: DENY</p></section>;
}
