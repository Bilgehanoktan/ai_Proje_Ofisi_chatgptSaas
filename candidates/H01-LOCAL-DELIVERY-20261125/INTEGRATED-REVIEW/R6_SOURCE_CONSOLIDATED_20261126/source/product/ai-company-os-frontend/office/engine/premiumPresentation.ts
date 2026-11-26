/** D0 presentation only. Fixed atlas geometry; no OfficeV0 placement authority. */
import {roles,type Role,type Actor} from './premiumModel';
export const FRAME=96, FOOT=80, COLS=12;
export const clips={idle:{frames:4,ms:240},walk:{frames:8,ms:90},work:{frames:4,ms:170},meeting:{frames:4,ms:220},rest:{frames:2,ms:400}} as const;
export type Clip=keyof typeof clips;
export type FrameSpec={name:string;role:Role;dir:1|-1;clip:Clip;index:number;x:number;y:number};
export const frames:readonly FrameSpec[]=roles.flatMap(role=>([-1,1] as const).flatMap(dir=>(Object.keys(clips) as Clip[]).flatMap(clip=>Array.from({length:clips[clip].frames},(_,index)=>({name:`${role}:${dir}:${clip}:${index}`,role,dir,clip,index}))))).map((f,i)=>({...f,x:i%COLS*FRAME,y:Math.floor(i/COLS)*FRAME}));
export const atlasSize={w:COLS*FRAME,h:Math.ceil(frames.length/COLS)*FRAME};
export function avatarFrame(a:Pick<Actor,'role'|'direction'|'mode'|'progress'>,time:number,animated:boolean){
 const clip:Clip=a.progress>0?'walk':a.mode;const c=clips[clip];const index=animated&&Number.isFinite(time)?Math.floor(Math.max(0,time)/c.ms)%c.frames:0;
 return `${a.role}:${a.direction}:${clip}:${index}`;
}
export type Point={x:number;y:number};
export type GlassSegment={a:Point;b:Point;height:number};
/** Screen/world-space occlusion approximation for decorative glass only, not physical collision. */
export function glassAlpha(w:GlassSegment,feet:Point,selected:boolean){
 if(!selected||!Number.isFinite(feet.x)||!Number.isFinite(feet.y))return .68;
 const dx=w.b.x-w.a.x;if(dx===0||w.height<=0)return .68;
 const t=(feet.x-w.a.x)/dx;if(t<0||t>1)return .68;
 const base=w.a.y+(w.b.y-w.a.y)*t;
 return feet.y<=base&&feet.y>=base-w.height-12?.16:.68;
}
export function monitorGlow(time:number,animated:boolean){return animated&&Number.isFinite(time)?.16+.06*(1+Math.sin(time/700))/2:.16;}
