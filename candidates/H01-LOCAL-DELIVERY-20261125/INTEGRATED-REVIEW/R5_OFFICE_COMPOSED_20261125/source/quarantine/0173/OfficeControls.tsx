"use client";
type Display='scene'|'list'|'engine';
type Floor={id:string;name:string;stations:readonly unknown[]};
export default function OfficeControls({floors,floorId,display,onFloor,onDisplay}:{floors:readonly Floor[];floorId:string;display:Display;onFloor:(id:string)=>void;onDisplay:(d:Display)=>void}){
 return <div className="eds-office-controls"><div role="group" aria-label="Kat seçimi">{floors.map((f,i)=><button type="button" key={f.id} aria-pressed={floorId===f.id} onClick={()=>onFloor(f.id)}>{String(i+1).padStart(2,'0')} · {f.name} · {f.stations.length} rezerv istasyon</button>)}</div><div role="group" aria-label="Görünüm">{([['scene','Sahne'],['engine','Geometri stüdyosu'],['list','Liste']] as const).map(([d,label])=><button type="button" key={d} aria-pressed={display===d} onClick={()=>onDisplay(d)}>{label}</button>)}</div><small>STATIC_ONLY · JOIN_HOLD</small></div>;
}
