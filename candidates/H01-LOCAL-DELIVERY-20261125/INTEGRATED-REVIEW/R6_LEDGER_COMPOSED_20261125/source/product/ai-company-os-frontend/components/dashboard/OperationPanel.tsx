"use client";
import type {ReactNode} from 'react';
export const panelTabs=['Aktivite','Ajanlar','Onaylar','Seçili Bağlam'] as const;
export type Panel=typeof panelTabs[number];
export default function OperationPanel({panel,onPanel,stations,detail}:{panel:Panel;onPanel:(panel:Panel)=>void;stations:ReactNode;detail:ReactNode}){
 return <section className="panel operation-panel" aria-label="Operasyon paneli"><div className="bar"><h2>Operasyon paneli</h2><span className="sub">SALT OKUNUR</span></div><div className="tabs" aria-label="Operasyon görünümü">{panelTabs.map(t=><button key={t} aria-pressed={panel===t} onClick={()=>onPanel(t)}>{t}</button>)}</div>{panel==='Ajanlar'?stations:panel==='Seçili Bağlam'?detail:<div className="empty" role="status">{panel==='Onaylar'?'Gerçek karar yok · HOLD':'Gerçek olay akışı yok · UNKNOWN'}</div>}</section>;
}
