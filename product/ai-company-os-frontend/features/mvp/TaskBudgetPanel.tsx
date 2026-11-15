"use client";
import {useEffect,useRef,useState} from 'react';
import {parseTaskBudgetProjection,type TaskBudgetProjection} from './taskBudgetProjection';
export default function TaskBudgetPanel(){
 const [data,setData]=useState<TaskBudgetProjection|null>(null),[status,setStatus]=useState('Henüz okunmadı · HOLD');
 const pending=useRef<AbortController|null>(null);
 useEffect(()=>()=>pending.current?.abort(),[]);
 async function read(){
  pending.current?.abort();const c=new AbortController();pending.current=c;setData(null);setStatus('Ortak örnek okunuyor…');
  try{const r=await fetch('/api/demo/task-budget',{cache:'no-store',redirect:'error',signal:c.signal});const x=r.ok?parseTaskBudgetProjection(await r.json()):null;if(c.signal.aborted)return;if(!x)throw Error('contract');setData(x);setStatus('Eşleştirilmiş tarihsel örnek · DENY');}
  catch{if(!c.signal.aborted)setStatus('Ortak kimlik yok, değişti veya uyumsuz · HOLD');}
 }
 return <section className="item" aria-label="Ortak görev ve bütçe örneği"><div className="bar"><div><h3>Görev ve bütçe bağlantısı · D0</h3><p className="sub">İki ayrı örnek deposu; atomik T1 veya canlı görev durumu değil.</p></div><button type="button" onClick={read}>Ortak kayıt oku</button></div><p role="status">{status}</p>{data&&<dl><div><dt>Görev</dt><dd>Research · {data.research_event_seq===null?'Bekleyen örnek':'Olay '+data.research_event_seq}</dd></div><div><dt>Ofis olayları</dt><dd>{data.office.sample_event_count}/5</dd></div><div><dt>Admission</dt><dd>{data.budget.phase}</dd></div><div><dt>Örnek rezervasyon / kalan</dt><dd>{data.budget.sample_reserved_minor} / {data.budget.sample_remaining_minor}</dd></div><div><dt>Örnek kimliği</dt><dd>{data.pair_id}</dd></div></dl>}<p>Nedensellik kanıtlanmadı · Lease ve geometri HOLD · Gerçek harcama/yürütme DENY</p></section>;
}
