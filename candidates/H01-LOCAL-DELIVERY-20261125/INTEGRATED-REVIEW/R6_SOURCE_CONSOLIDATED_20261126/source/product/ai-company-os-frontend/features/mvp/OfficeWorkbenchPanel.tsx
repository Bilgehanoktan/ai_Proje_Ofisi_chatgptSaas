"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import TaskBudgetPanel from './TaskBudgetPanel';
export default function OfficeWorkbenchPanel(){
 const {state:readState,data,read}=useProjectionRead('office-workbench');
 const status=readStatus(readState,{"idle":"Örnek okunmadı · HOLD","loading":"Yerel kayıt okunuyor…","historical":"Tarihsel sentetik kayıt · DENY","hold":"Örnek yok veya kayıt uyuşmuyor · HOLD"});
 return <><section className="item" aria-label="İstasyon görev gözlemleri"><div className="bar"><div><h3>İstasyon görev gözlemleri · D0</h3><p className="sub">Kalıcı örnek olaylar; aktif ajan veya canlı konum değil.</p></div><button type="button" onClick={read}>Kayıt oku</button></div><p role="status" className="projection-read-status" data-phase={readState.phase}>{status}</p>{data&&<div className="sectiongrid">{data.roles.map(r=><article className="item" key={r.station_id}><h3>{r.role}</h3><p>{r.observed}/{r.total} örnek gözlem</p><small>{r.station_id} · {r.observed===r.total?'Örnek gözlemleri tamam':'Örnek gözlemleri eksik'}</small></article>)}</div>}<p>Görev gözlemi ≠ ajan çalışma durumu · Layout JOIN_HOLD.</p><p>IV / Release / Geometri: HOLD · Gerçek yürütme: DENY</p></section><TaskBudgetPanel/></>;
}
