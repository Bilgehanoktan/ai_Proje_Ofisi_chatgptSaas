"use client";
import {useEffect,useRef,useState} from 'react';
import {parseAdmissionProjection,type AdmissionProjection} from './admissionProjection';
export default function AdmissionProjectionPanel(){
 const [data,setData]=useState<AdmissionProjection|null>(null),[status,setStatus]=useState('Henüz okunmadı · HOLD');
 const pending=useRef<AbortController|null>(null);
 useEffect(()=>()=>pending.current?.abort(),[]);
 async function read(){
  pending.current?.abort();const c=new AbortController();pending.current=c;setData(null);setStatus('Sentetik kayıt okunuyor…');
  try{const r=await fetch('/api/demo/admission',{cache:'no-store',redirect:'error',signal:c.signal});const x=r.ok?parseAdmissionProjection(await r.json()):null;if(c.signal.aborted)return;if(!x)throw Error('contract');setData(x);setStatus('Sentetik okuma · DENY');}
  catch{if(!c.signal.aborted)setStatus('Örnek yok veya sözleşme uyumsuz · HOLD');}
 }
 return <section className="panel" aria-label="Sentetik admission ve bütçe"><div className="bar"><div><h2>Admission ve bütçe · D0</h2><p className="sub">Örnek minor-unit değerleri · gerçek maliyet veya izin değil</p></div><button type="button" onClick={read}>Kayıt oku</button></div><p role="status">{status}</p>{data&&<dl><div><dt>Durum</dt><dd>{data.phase}</dd></div><div><dt>Örnek rezervasyon</dt><dd>{data.sample_reserved_minor}</dd></div><div><dt>Örnek gözlenen</dt><dd>{data.sample_observed_minor}</dd></div><div><dt>Örnek kalan</dt><dd>{data.sample_remaining_minor}</dd></div></dl>}<p>Gerçek işlem / harcama / yayın: DENY</p></section>;
}
