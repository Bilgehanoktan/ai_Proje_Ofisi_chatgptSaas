"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
export default function AdmissionProjectionPanel(){
 const {state:readState,data,read}=useProjectionRead('admission');
 const status=readStatus(readState,{"idle":"Henüz okunmadı · HOLD","loading":"Sentetik kayıt okunuyor…","historical":"Sentetik okuma · DENY","hold":"Örnek yok veya sözleşme uyumsuz · HOLD"});
 return <section className="panel" aria-label="Sentetik admission ve bütçe"><div className="bar"><div><h2>Admission ve bütçe · D0</h2><p className="sub">Örnek minor-unit değerleri · gerçek maliyet veya izin değil</p></div><button type="button" onClick={read}>Kayıt oku</button></div><p role="status" className="projection-read-status" data-phase={readState.phase}>{status}</p>{data&&<dl><div><dt>Durum</dt><dd>{data.phase}</dd></div><div><dt>Örnek rezervasyon</dt><dd>{data.sample_reserved_minor}</dd></div><div><dt>Örnek gözlenen</dt><dd>{data.sample_observed_minor}</dd></div><div><dt>Örnek kalan</dt><dd>{data.sample_remaining_minor}</dd></div></dl>}<p>Gerçek işlem / harcama / yayın: DENY</p></section>;
}
