/** A4 D0 render bridge: never advances A3 until the preceding visual edge completes. */
import {createVisualIdentityRegistry} from './premiumActorIdentity';
import {createIdentityTraffic,type Registry} from './premiumIdentityTraffic';
import type {Cell,Layout} from './premiumHybridLayout';
export const EDGE_MS=240;
export const isoHybrid=(layout:Layout,x:number,y:number)=>({x:96+(layout.height-1+x-y)*32,y:120+(x+y)*16});
export function hybridBounds(layout:Layout){return {width:(layout.width+layout.height)*32+192,height:(layout.width+layout.height)*16+240};}
export function fitHybrid(layout:Layout,width:number,height:number){const b=hybridBounds(layout);return Math.min(width/b.width,height/b.height);}
export function createHybridRender(registry:Registry=createVisualIdentityRegistry()){
 const traffic=createIdentityTraffic(registry);let current=traffic.snapshot(),elapsed=EDGE_MS;
 const active=()=>elapsed<EDGE_MS;
 const frame=()=>{const progress=active()?elapsed/EDGE_MS:1;return Object.freeze({tick:current.token.tick,status:current.status,reason:current.reason,interpolating:active(),actors:Object.freeze(current.actors.map(a=>{const identity=registry.actor(a.visualActorId)!;const m=current.movements.find(m=>m.visualActorId===a.visualActorId);const from=m?.from??a.cell,to=m?.to??a.cell;return Object.freeze({id:a.visualActorId,role:identity.roleTemplateId,assetProfileId:identity.assetProfileId,stationId:identity.stationId,cell:a.cell,x:from[0]+(to[0]-from[0])*progress,y:from[1]+(to[1]-from[1])*progress,moving:active()&&!!m,direction:(to[0]-from[0]-(to[1]-from[1])<0?-1:1) as 1|-1,atStation:(!m||!active())&&a.cell[0]===identity.anchor[0]&&a.cell[1]===identity.anchor[1]});}))});};
 function advance(ms:number,paused=false){if(paused||!Number.isFinite(ms)||ms<=0)return frame();if(active()){elapsed=Math.min(EDGE_MS,elapsed+Math.min(ms,EDGE_MS));return frame();}if(current.status!=='READY'&&current.status!=='HOLD'){current=traffic.advance(current.token);elapsed=current.movements.length?0:EDGE_MS;}return frame();}
 function goal(id:string,target:Cell){if(active())return false;try{current=traffic.setGoals(current.token,[{visualActorId:id,cell:target}]);return true;}catch{return false;}}
 function home(id:string){const actor=registry.actor(id);return actor?goal(id,actor.anchor):false;}
 return Object.freeze({registry,frame,advance,goal,home});
}
