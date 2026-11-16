// D0 presentation-only layout. Never join these coordinates to OfficeV0.
import {pairEscape,type EscapeStep} from './premiumRouting';
export const roles = ['orchestrator','research','engineer','qa'] as const;
export type Role = typeof roles[number];
export type Mode = 'idle'|'work'|'meeting'|'rest';
export type Cell = readonly [number,number];
export type Actor = {role:Role; cell:Cell; mode:Mode; target:Mode; path:Cell[]; progress:number; direction:1|-1};
export const WIDTH=12, HEIGHT=10;
export const palette:Record<Role,number>={orchestrator:0x627fae,research:0x4b9d87,engineer:0x9977cc,qa:0xc68e59};
export const rooms=[{name:'CEO / Strategy',x:0,y:0,w:5,h:4,color:0x695749},{name:'Boardroom',x:7,y:0,w:5,h:4,color:0x425a68},{name:'Engineering / Research',x:0,y:6,w:5,h:4,color:0x4b6670},{name:'QA / Lounge',x:7,y:6,w:5,h:4,color:0x5c536f}] as const;
export const iso=(x:number,y:number)=>({x:550+(x-y)*36,y:115+(x+y)*18});
const key=(c:Cell)=>c.join(',');
const equal=(a:Cell,b:Cell)=>key(a)===key(b);
const work:Record<Role,Cell>={orchestrator:[2,2],research:[1,7],engineer:[3,8],qa:[9,7]};
const meeting:Record<Role,Cell>={orchestrator:[8,2],research:[9,2],engineer:[10,2],qa:[10,1]};
const rest:Record<Role,Cell>={orchestrator:[8,8],research:[10,8],engineer:[8,9],qa:[10,9]};
export const furniture=[{x:2,y:1,w:2,h:1,kind:'executive'},{x:8,y:0,w:3,h:1,kind:'table'},{x:1,y:6,w:1,h:1,kind:'desk'},{x:3,y:7,w:1,h:1,kind:'desk'},{x:9,y:6,w:1,h:1,kind:'desk'},{x:7,y:9,w:1,h:1,kind:'sofa'},{x:11,y:9,w:1,h:1,kind:'plant'}] as const;
const blocked=new Set<string>();for(const f of furniture)for(let x=f.x;x<f.x+f.w;x++)for(let y=f.y;y<f.y+f.h;y++)blocked.add(key([x,y]));
export function walkable(c:Cell){return Number.isInteger(c[0])&&Number.isInteger(c[1])&&c[0]>=0&&c[0]<WIDTH&&c[1]>=0&&c[1]<HEIGHT&&!blocked.has(key(c));}
export function pathBetween(a:Cell,b:Cell,occupied:ReadonlySet<string>=new Set()):Cell[]|null{
 if(!walkable(a)||!walkable(b)||occupied.has(key(b)))return null;
 const q:Cell[]=[a],prev=new Map<string,Cell|null>([[key(a),null]]);
 for(let i=0;i<q.length;i++){const c=q[i];if(equal(c,b)){const out:Cell[]=[];let n:Cell|null=c;while(n){out.unshift(n);n=prev.get(key(n))??null;}return out;}
 for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){const n:Cell=[c[0]+dx,c[1]+dy],k=key(n);if(walkable(n)&&!occupied.has(k)&&!prev.has(k)){prev.set(k,c);q.push(n);}}}return null;
}
export function initialActors():Actor[]{return roles.map(role=>({role,cell:work[role],mode:'idle',target:'idle',path:[],progress:0,direction:1}));}
const destination=(r:Role,m:Mode)=>m==='meeting'?meeting[r]:m==='rest'?rest[r]:work[r];
type Recovery={pair:readonly [Actor,Actor];steps:EscapeStep[]};
type Scheduler={cursor:number;recovery:Recovery|null;blocked:boolean;retryAt:number;tick:number};
const schedulers=new WeakMap<Actor[],Scheduler>();
function scheduler(a:Actor[]):Scheduler{let s=schedulers.get(a);if(!s){s={cursor:0,recovery:null,blocked:false,retryAt:0,tick:0};schedulers.set(a,s);}return s;}
export function routeStatus(a:Actor[]){const s=scheduler(a);return s.recovery?'COOPERATIVE_ESCAPE':s.blocked?'WAIT_BLOCKED':a.some(v=>v.progress>0)?'MOVING':'READY';}
export function command(actors:Actor[],role:Role,mode:Mode):boolean{
 const a=actors.find(v=>v.role===role);if(!a||!['idle','work','meeting','rest'].includes(mode))return false;
 if(a.progress>0)return false;
 const s=scheduler(actors);s.recovery=null;s.retryAt=0;s.blocked=false;
 a.target=mode;a.mode='idle';a.path=[];return true;
}
function begin(a:Actor,to:Cell){a.path=[to];a.mode='idle';a.direction=iso(...to).x>=iso(...a.cell).x?1:-1;}
function move(a:Actor,dt:number){if(!a.path[0])return;a.progress+=dt*2.4;if(a.progress>=1){a.cell=a.path[0];a.path=[];a.progress=0;if(equal(a.cell,destination(a.role,a.target)))a.mode=a.target;}}
function findRecovery(actors:Actor[],order:Actor[]):Recovery|null{
 for(let i=0;i<order.length;i++)for(let j=i+1;j<order.length;j++){
  const a=order[i],b=order[j],ga=destination(a.role,a.target),gb=destination(b.role,b.target);
  if(equal(a.cell,ga)&&equal(b.cell,gb))continue;
  const fixed=new Set(actors.filter(v=>v!==a&&v!==b).map(v=>key(v.cell)));
  const steps=pairEscape([a.cell,b.cell],[ga,gb],walkable,fixed);
  if(steps?.length)return {pair:[a,b],steps};
 }return null;
}
export function advance(actors:Actor[],seconds:number):void{
 const dt=Math.max(0,Math.min(.1,Number.isFinite(seconds)?seconds:0));if(dt===0||!actors.length)return;
 const s=scheduler(actors);s.tick++;s.blocked=false;
 if(s.recovery){
  const moving=actors.find(a=>a.progress>0);if(moving){move(moving,dt);return;}
  const step=s.recovery.steps.shift();if(step){const a=s.recovery.pair[step.actor],to=step.to;
   if(walkable(to)&&Math.abs(to[0]-a.cell[0])+Math.abs(to[1]-a.cell[1])===1&&!actors.some(v=>v!==a&&equal(v.cell,to))){begin(a,to);move(a,dt);return;}
  }s.recovery=null;
 }
 const order=actors.map((_,i)=>actors[(i+s.cursor)%actors.length]);s.cursor=(s.cursor+1)%actors.length;
 const occupied=new Set(actors.map(a=>key(a.cell)));for(const a of actors)if(a.progress>0&&a.path[0])occupied.add(key(a.path[0]));
 let moved=false;
 for(const a of order){const dest=destination(a.role,a.target);
  if(a.progress===0){if(equal(a.cell,dest)){a.mode=a.target;a.path=[];continue;}const reserved=new Set(occupied);reserved.delete(key(a.cell));const p=pathBetween(a.cell,dest,reserved);a.path=p?.slice(1,2)??[];if(!a.path.length)continue;occupied.add(key(a.path[0]));begin(a,a.path[0]);}
  if(a.path[0]){moved=true;move(a,dt);}
 }
 if(!moved&&actors.some(a=>!equal(a.cell,destination(a.role,a.target)))){s.blocked=true;if(s.tick>=s.retryAt){s.recovery=findRecovery(actors,order);s.retryAt=s.tick+30;if(s.recovery)s.blocked=false;}}
}
export function position(a:Actor){const from=iso(...a.cell),to=a.path[0]?iso(...a.path[0]):from;return {x:from.x+(to.x-from.x)*a.progress,y:from.y+(to.y-from.y)*a.progress};}
// Explicit no-join boundary: even a structurally valid readback cannot drive this scene.
export function projectionBoundary(_readback:unknown){return {status:'JOIN_HOLD',authoritative:false,placement:false,taskBinding:false,actors:[] as readonly never[]} as const;}
