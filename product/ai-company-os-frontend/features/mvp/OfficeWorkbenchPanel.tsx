"use client";
import {useEffect,useRef,useState} from 'react';
import TaskBudgetPanel from './TaskBudgetPanel';
import {parseOfficeWorkbench,type OfficeWorkbench} from './officeWorkbenchProjection';
export default function OfficeWorkbenchPanel(){
 const [data,setData]=useState<OfficeWorkbench|null>(null),[status,setStatus]=useState('Örnek okunmadı · HOLD');
 const pending=useRef<AbortController|null>(null);
 useEffect(()=>()=>pending.current?.abort(),[]);
 async function read(){
  pending.current?.abort();const c=new AbortController();pending.current=c;setData(null);setStatus('Yerel kayıt okunuyor…');
  try{const r=await fetch('/api/demo/office-workbench',{cache:'no-store',redirect:'error',signal:c.signal});const x=r.ok?parseOfficeWorkbench(await r.json()):null;if(c.signal.aborted)return;if(!x)throw Error('contract');setData(x);setStatus('Tarihsel sentetik kayıt · DENY');}
  catch{if(!c.signal.aborted)setStatus('Örnek yok veya kayıt uyuşmuyor · HOLD');}
 }
 return <><section className="item" aria-label="İstasyon görev gözlemleri"><div className="bar"><div><h3>İstasyon görev gözlemleri · D0</h3><p className="sub">Kalıcı örnek olaylar; aktif ajan veya canlı konum değil.</p></div><button type="button" onClick={read}>Kayıt oku</button></div><p role="status">{status}</p>{data&&<div className="sectiongrid">{data.roles.map(r=><article className="item" key={r.station_id}><h3>{r.role}</h3><p>{r.observed}/{r.total} örnek gözlem</p><small>{r.station_id}</small></article>)}</div>}<p>IV / Release / Geometri: HOLD · Gerçek yürütme: DENY</p></section><TaskBudgetPanel/></>;
}
