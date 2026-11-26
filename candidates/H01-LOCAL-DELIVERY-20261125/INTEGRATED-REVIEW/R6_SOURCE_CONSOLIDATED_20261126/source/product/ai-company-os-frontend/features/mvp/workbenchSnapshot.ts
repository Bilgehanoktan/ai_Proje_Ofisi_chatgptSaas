/** Strict viewer for the 0182 fixed synthetic CLI snapshot. Not an authority. */
const ids = ['draft','iv','merge','plan','qa','release','research'];
const order = ['plan','draft','research','merge','qa'];
const pin = '6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9';
const keys = ['mode','tenant','company','plan_digest','tasks','events','admission','dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted'];
export type SampleTask = [string, 'PENDING'|'OBSERVED', 0|1];
export type SampleSnapshot = { tasks: SampleTask[]; events: number };
export function parseWorkbenchSnapshot(raw: string): SampleSnapshot|null {
 if (typeof raw !== 'string' || raw.length > 20000) return null;
 try {
  const x = JSON.parse(raw);
  if (!x || typeof x !== 'object' || Array.isArray(x) || Object.keys(x).length !== keys.length || !keys.every(k=>Object.hasOwn(x,k))) return null;
  if (x.mode !== 'D0_WORKBENCH_0182' || x.tenant !== 'synthetic-tenant' || x.company !== 'synthetic-company' || x.plan_digest !== pin || x.admission !== 'DENY' || ['dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted'].some(k=>x[k]!==false)) return null;
  if (!Array.isArray(x.tasks) || x.tasks.length !== 7 || !Array.isArray(x.events) || x.events.length > 5) return null;
  const tasks: SampleTask[] = [];
  for(let i=0;i<ids.length;i++) {
   const t=x.tasks[i];
   if(!Array.isArray(t)||t.length!==3||t[0]!==ids[i]||!((t[1]==='PENDING'&&t[2]===0)||(t[1]==='OBSERVED'&&t[2]===1&&order.includes(t[0])))) return null;
   tasks.push([t[0],t[1],t[2]]);
  }
  // Viewer deliberately accepts only the CLI demo's exact prefix order, not arbitrary workbench histories.
  for(let i=0;i<x.events.length;i++) {
   const e=x.events[i];
   if(!Array.isArray(e)||e.length!==5||e[0]!==i+1||e[1]!==order[i]||e[2]!==1||e[3]!==i+1||typeof e[4]!=='string'||!/^[a-f0-9]{64}$/.test(e[4])) return null;
  }
  if(tasks.some(t=>(t[1]==='OBSERVED')!==order.slice(0,x.events.length).includes(t[0]))) return null;
  return {tasks,events:x.events.length};
 } catch {return null;}
}
