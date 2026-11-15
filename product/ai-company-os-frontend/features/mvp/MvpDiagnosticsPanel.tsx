"use client";
import {useProjectionRead} from '../data/useProjectionRead';
import {readStatus} from '../data/projectionRead';
import {parseMvpDiagnostics} from './mvpDiagnostics';
export default function MvpDiagnosticsPanel(){
 const {state:readState,data,read}=useProjectionRead('mvp',parseMvpDiagnostics);
 const state=readStatus(readState,{"idle":"Henüz okunmadı · HOLD","loading":"Yerel sentetik tanılama okunuyor…","historical":"Sentetik backend okuması · DENY / HOLD","hold":"Backend erişilemiyor veya sözleşme uyumsuz · HOLD"});
 return <section className="panel" aria-label="Yerel MVP tanılama"><div className="bar"><div><h2>Yerel MVP tanılama</h2><p className="sub">Salt okunur · gerçek ajan, finans veya yetki yok</p></div><button type="button" onClick={read}>Sentetik backend oku</button></div><p role="status" className="projection-read-status" data-phase={readState.phase}>{state}</p>{data&&<><p>Plan: {data.plan_digest.slice(0,12)}…</p><dl>{Object.entries(data.sections).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><p>SQLite örnek satır: {data.sample_event_rows??'—'} · Sentetik kalan kapasite (minor): {data.diagnostic_remaining_minor??'—'}</p></>}</section>;
}
