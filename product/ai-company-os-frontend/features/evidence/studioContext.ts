/** Presentation from an already validated reference plan or demo geometry only. */
export type StudioTask={id:string;label:string;role:string;depends_on:readonly string[]};
export type StudioStation={id:string;room:string;role:string};
export function roleTaskContext(tasks:readonly StudioTask[],role:string){
 const labels=new Map(tasks.map(t=>[t.id,t.label]));
 return tasks.filter(t=>t.role===role).map(t=>({id:t.id,label:t.label,predecessors:t.depends_on.map(id=>({id,label:labels.get(id)??id})),followers:tasks.filter(next=>next.depends_on.includes(t.id)).map(next=>({id:next.id,label:next.label}))}));
}
export function roomStations<T extends StudioStation>(stations:readonly T[],room:string|null):T[]{
 return stations.filter(s=>room===null||s.room===room);
}
export function selectedRoom<T extends {id:string}>(rooms:readonly T[],id:string|null):T|undefined{
 return id===null?undefined:rooms.find(room=>room.id===id);
}
