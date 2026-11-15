"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import {parseTaskBudgetProjection} from './taskBudgetProjection';
export default function TaskBudgetPanel(){
 const {state:readState,data,read}=useProjectionRead('task-budget',parseTaskBudgetProjection);
 const status=readStatus(readState,{"idle":"Henüz okunmadı · HOLD","loading":"Ortak örnek okunuyor…","historical":"Eşleştirilmiş tarihsel örnek · DENY","hold":"Ortak kimlik yok, değişti veya uyumsuz · HOLD"});
 return <section className="item" aria-label="Ortak görev ve bütçe örneği"><div className="bar"><div><h3>Görev ve bütçe bağlantısı · D0</h3><p className="sub">İki ayrı örnek deposu; atomik T1 veya canlı görev durumu değil.</p></div><button type="button" onClick={read}>Ortak kayıt oku</button></div><p role="status" className="projection-read-status" data-phase={readState.phase}>{status}</p>{data&&<dl><div><dt>Görev</dt><dd>Research · {data.research_event_seq===null?'Bekleyen örnek':'Olay '+data.research_event_seq}</dd></div><div><dt>Ofis olayları</dt><dd>{data.office.sample_event_count}/5</dd></div><div><dt>Admission</dt><dd>{data.budget.phase}</dd></div><div><dt>Örnek rezervasyon / kalan</dt><dd>{data.budget.sample_reserved_minor} / {data.budget.sample_remaining_minor}</dd></div><div><dt>Örnek kimliği</dt><dd>{data.pair_id}</dd></div></dl>}<p>Nedensellik kanıtlanmadı · Lease ve geometri HOLD · Gerçek harcama/yürütme DENY</p></section>;
}
