import {historicalEvents,diagnosticFindings} from './historicalEvidence';
export function reviewTimeline(endpoint:string,phase:string,data:unknown,query:string,state:string,newest:boolean){
 const events=historicalEvents(endpoint,phase,data);
 const q=query.trim().toLowerCase();
 const states=[...new Set(events.map(e=>e.state))];
 const rows=events.filter(e=>(!state||e.state===state)&&(`${e.kind} ${e.state} ${e.version}`).toLowerCase().includes(q));
 return {total:events.length,states,rows:newest?[...rows].reverse():rows};
}
export function reviewEngines(endpoint:string,phase:string,data:unknown,query:string){
 const findings=diagnosticFindings(endpoint,phase,data),q=query.trim().toLowerCase();
 return findings.filter(f=>`${f.engine} ${f.reason}`.toLowerCase().includes(q));
}
