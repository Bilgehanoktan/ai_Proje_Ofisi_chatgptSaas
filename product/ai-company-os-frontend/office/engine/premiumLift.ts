/** Isolated D0 lift protocol prototype. Never moves actual actors or activates reserved floor. */
import {roles,type Role} from './premiumModel';
export type Floor=1|2;
export type LiftRequest={role:Role;from:Floor;to:Floor};
export type Lift={floor:Floor;phase:'idle'|'positioning'|'boarding'|'travel'|'exit';remaining:number;active:LiftRequest|null;queue:LiftRequest[]};
export const initialLift=():Lift=>({floor:1,phase:'idle',remaining:0,active:null,queue:[]});
export function enqueueLift(s:Lift,r:LiftRequest):boolean{
 if(!roles.includes(r.role)||![1,2].includes(r.from)||![1,2].includes(r.to)||r.from===r.to||s.active?.role===r.role||s.queue.some(q=>q.role===r.role)||s.queue.length>=4)return false;
 s.queue.push({...r});return true;
}
export function cancelLift(s:Lift,role:Role){const i=s.queue.findIndex(r=>r.role===role);if(i<0)return false;s.queue.splice(i,1);return true;}
/** Every tick yields at most one arrival; exit stays reserved until landing is free. */
export function tickLift(s:Lift,seconds:number,landingFree:(floor:Floor,role:Role)=>boolean):LiftRequest|null{
 const dt=Number.isFinite(seconds)?Math.max(0,Math.min(seconds,.25)):0;if(!dt)return null;
 if(s.phase==='idle'){const r=s.queue.shift();if(!r)return null;s.active=r;s.phase=s.floor===r.from?'boarding':'positioning';s.remaining=s.phase==='boarding'?.5:1.5;return null;}
 const r=s.active;if(!r)throw Error('LIFT_STATE_INVALID');s.remaining=Math.max(0,s.remaining-dt);if(s.remaining>0)return null;
 if(s.phase==='positioning'){s.floor=r.from;s.phase='boarding';s.remaining=.5;}
 else if(s.phase==='boarding'){s.phase='travel';s.remaining=1.5;}
 else if(s.phase==='travel'){s.floor=r.to;s.phase='exit';s.remaining=.5;}
 else if(s.phase==='exit'&&landingFree(r.to,r.role)){s.active=null;s.phase='idle';return {...r};}
 return null;
}
