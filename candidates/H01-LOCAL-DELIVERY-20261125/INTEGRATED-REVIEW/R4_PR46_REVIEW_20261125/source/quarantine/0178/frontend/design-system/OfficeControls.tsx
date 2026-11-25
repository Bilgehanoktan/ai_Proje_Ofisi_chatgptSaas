"use client";
import type {ReactNode} from 'react';
type Display='scene'|'list'|'engine';
type Floor={id:string;name:string;stations:readonly unknown[]};
export function FloorControls({floors,floorId,onFloor}:{floors:readonly Floor[];floorId:string;onFloor:(id:string)=>void}){
 return <div className="floor-switch" role="group" aria-label="Kat seçimi">{floors.map((f,i)=><button type="button" key={f.id} aria-pressed={floorId===f.id} onClick={()=>onFloor(f.id)}><span>{String(i+1).padStart(2,'0')}</span>{f.name}<small>{f.stations.length} istasyon</small></button>)}</div>;
}
export function DisplayControls({display,onDisplay,children}:{display:Display;onDisplay:(d:Display)=>void;children?:ReactNode}){
 return <div className="chips" role="group" aria-label="Ofis görünümü">{([['scene','Sahne'],['engine','Geometri stüdyosu'],['list','Liste']] as const).map(([d,label])=><button type="button" key={d} aria-pressed={display===d} onClick={()=>onDisplay(d)}>{label}</button>)}{children}</div>;
}
