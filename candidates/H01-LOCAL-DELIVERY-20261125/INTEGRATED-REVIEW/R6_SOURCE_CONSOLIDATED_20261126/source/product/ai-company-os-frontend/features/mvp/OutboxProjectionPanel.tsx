"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
export default function OutboxProjectionPanel(){
 const {state:readState,data,read}=useProjectionRead('outbox');
 const state=readStatus(readState,{"idle":"Henüz okunmadı · HOLD","loading":"Yerel sentetik Outbox okunuyor…","historical":"Sentetik okuma · DENY","hold":"Yerel örnek yok veya sözleşme uyumsuz · HOLD"});
 return <section className="panel" aria-label="Sentetik Outbox mutabakatı"><div className="bar"><div><h2>Outbox inceleme · D0</h2><p className="sub">Salt okunur örnek · claim gönderim yetkisi değildir</p></div><button type="button" onClick={read}>Outbox oku</button></div><p role="status" className="projection-read-status" data-phase={readState.phase}>{state}</p>{data&&<dl><div><dt>İnceleme durumu</dt><dd>{data.phase}</dd></div><div><dt>İnceleme nesli</dt><dd>{data.generation??'—'}</dd></div><div><dt>Örnek readback kaydı</dt><dd>{data.readback_recorded?'Var · HOLD':'Yok'}</dd></div></dl>}<p>Gönderim / yeniden deneme / yayın: DENY</p></section>;
}
