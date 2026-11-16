import type {GameObjects} from 'phaser';
import {iso,palette,position,type Actor,type furniture} from '../engine/premiumModel';
import {depthAt} from '../engine/premiumRouting';
type G=GameObjects.Graphics;
type Point={x:number;y:number};
const poly=(g:G,color:number,points:Point[],alpha=1)=>g.fillStyle(color,alpha).fillPoints(points,true);
/** Isometric box with three independently shaded faces; bottom anchor is in world space. */
function box(g:G,x:number,y:number,w:number,d:number,h:number,top:number,left:number,right:number){
 const a={x:x-w,y:y-d-h},b={x,y:y-2*d-h},c={x:x+w,y:y-d-h},e={x,y:y-h};
 poly(g,left,[a,e,{x,y},{x:a.x,y:a.y+h}]);poly(g,right,[e,c,{x:c.x,y:c.y+h},{x,y}]);poly(g,top,[a,b,c,e]);
}
/** Each occupied tile owns a visual segment, so long objects do not sort as one midpoint. */
export function drawFurnitureCell(g:G,f:typeof furniture[number],x:number,y:number){
 const p=iso(x,y);const X=p.x,Y=p.y+10;
 g.fillStyle(0x101820,.45).fillEllipse(X,Y,53,24);
 if(f.kind==='plant'){
  box(g,X,Y-3,12,6,15,0xc1a58b,0x85684c,0x9d7d5a);g.lineStyle(3,0x4a6e58).lineBetween(X,Y-18,X,Y-53);
  for(const [dx,dy,r,c] of [[-11,-40,12,0x3f795f],[10,-43,13,0x639f72],[0,-55,12,0x82b77c],[-3,-35,13,0x517e5e]])g.fillStyle(c).fillEllipse(X+dx,Y+dy,r*1.7,r);
 }else if(f.kind==='sofa'){
  box(g,X,Y,25,12,11,0x9da7b7,0x58687e,0x6f8195);box(g,X-8,Y-7,18,9,21,0x8192a6,0x43576e,0x5a6d83);box(g,X+16,Y-2,8,5,15,0xb1bdc9,0x617387,0x8291a3);
  g.lineStyle(1,0xe1e7eb,.6).lineBetween(X-12,Y-12,X+10,Y-6);
 }else{
  const walnut=f.kind==='executive'||f.kind==='table';const top=walnut?0xc29c73:0xc3ced1;
  for(const dx of [-17,17])g.fillStyle(0x414e5c).fillRoundedRect(X+dx-3,Y-21,6,22,2);
  box(g,X,Y-17,29,13,6,top,walnut?0x76523c:0x788994,walnut?0x9a724f:0x99acb5);
  if(f.kind!=='table'&&(f.kind!=='executive'||x===f.x)){
   g.fillStyle(0x293b49).fillRoundedRect(X-15,Y-59,30,21,3).fillStyle(0x74bac5).fillRoundedRect(X-12,Y-56,24,15,2);
   g.lineStyle(1,0xd0f2ef,.8).lineBetween(X-9,Y-52,X+5,Y-52).lineBetween(X-9,Y-48,X+9,Y-48).lineBetween(X-9,Y-44,X+1,Y-44);
   g.fillStyle(0x243440).fillRect(X-2,Y-38,4,9).fillRoundedRect(X-8,Y-30,16,3,1);
   poly(g,0x354550,[{x:X-13,y:Y-28},{x:X,y:Y-34},{x:X+14,y:Y-28},{x:X,y:Y-22}]);g.fillStyle(0xf1d8a9).fillCircle(X+18,Y-31,3);
  }else{g.fillStyle(0xe7ddc8).fillRoundedRect(X-9,Y-35,18,9,2).fillStyle(0x495b68).fillRect(X-6,Y-32,11,2);}
 }
 g.setDepth(depthAt(Y,p.x,'furniture'));
}
export function drawAvatar(g:G,a:Actor,time:number,animated:boolean,selected:boolean){
 const p=position(a),x=p.x,y=p.y,moving=a.progress>0,seated=!moving&&a.mode!=='idle';
 const phase=animated?Math.sin(time/(moving?90:210)):0,leg=moving?phase*7:0,bob=moving?Math.abs(phase)*2:0,body=seated?18:29,head=y-body-28-bob;
 const roleColor=palette[a.role],skin={orchestrator:0xe3b798,research:0xc58e68,engineer:0xf0cba5,qa:0xa87354}[a.role];
 g.clear().fillStyle(0x09121c,.42).fillEllipse(x,y+3,31,13);
 if(selected)g.lineStyle(2,0xe6d5ff).strokeEllipse(x,y+4,38,17);
 if(seated){box(g,x,y+4,10,5,8,0x506778,0x2b3c4a,0x415564);g.fillStyle(0x334653).fillRoundedRect(x-9,y-body-5,18,18,4);}
 g.lineStyle(6,0x283847).lineBetween(x-5,y-body+5,x-6+leg,y-2).lineBetween(x+5,y-body+5,x+6-leg,y-2);
 g.fillStyle(0x14212d).fillRoundedRect(x-10+leg,y-4,10,5,2).fillRoundedRect(x+2-leg,y-4,10,5,2);
 g.fillStyle(0x203344).fillRoundedRect(x-12,y-body-17-bob,24,27,6).fillStyle(roleColor).fillRoundedRect(x-10,y-body-16-bob,20,24,5);
 poly(g,0xe8e6df,[{x:x-5,y:y-body-16-bob},{x:x+5,y:y-body-16-bob},{x,y:y-body-5-bob}]);g.fillStyle(0xe6f2ee).fillRoundedRect(x+4,y-body-8-bob,5,6,1);
 const hand= moving?leg*.65:a.mode==='work'?phase*3:0;
 g.lineStyle(6,roleColor).lineBetween(x-10,y-body-12-bob,x-14+hand,y-body+1).lineBetween(x+10,y-body-12-bob,x+14-hand,y-body+1);
 g.fillStyle(skin).fillCircle(x-14+hand,y-body+1,3.5).fillCircle(x+14-hand,y-body+1,3.5).fillRoundedRect(x-10,head-3,20,22,7);
 g.fillStyle(a.role==='qa'?0x262226:a.role==='research'?0x493629:0x3c302c).fillEllipse(x,head,22,13).fillRoundedRect(x-a.direction*7-3,head+1,6,11,2);
 g.fillStyle(0x263545).fillCircle(x+a.direction*4,head+8,1.6).fillCircle(x+a.direction*8,head+8,1.2);
 if(a.role==='engineer'){g.lineStyle(1.5,0xcedce6).strokeRoundedRect(x-7,head+4,7,7,2).strokeRoundedRect(x+1,head+4,7,7,2).lineBetween(x,head+7,x+1,head+7);}
 g.setDepth(depthAt(y,p.x,'actor'));
}
