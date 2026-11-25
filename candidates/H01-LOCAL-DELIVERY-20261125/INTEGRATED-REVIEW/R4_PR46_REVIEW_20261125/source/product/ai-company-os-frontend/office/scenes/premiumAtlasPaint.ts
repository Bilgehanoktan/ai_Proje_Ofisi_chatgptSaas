/** Original procedural vector art rendered into an actual browser Canvas atlas. */
import {FRAME,FOOT,frames,atlasSize,clips,type FrameSpec} from '../engine/premiumPresentation';
const art={orchestrator:['#627fae','#e3b798','#3c302c'],research:['#4b9d87','#c58e68','#493629'],engineer:['#9977cc','#f0cba5','#3c302c'],qa:['#c68e59','#a87354','#262226']} as const;
export function paintAvatar(c:CanvasRenderingContext2D,f:FrameSpec){
 const [coat,skin,hair]=art[f.role],seated=f.clip==='work'||f.clip==='meeting'||f.clip==='rest',walking=f.clip==='walk';
 const phase=Math.sin(f.index*2*Math.PI/clips[f.clip].frames),leg=walking?phase*7:0,bob=walking?Math.abs(phase)*2:f.clip==='idle'?phase*.8:0,body=seated?18:29,head=-body-27-bob;
 const round=(x:number,y:number,w:number,h:number,r:number,color:string)=>{c.fillStyle=color;c.beginPath();c.roundRect(x,y,w,h,r);c.fill();};
 const ellipse=(x:number,y:number,rx:number,ry:number,color:string)=>{c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();};
 const line=(x:number,y:number,X:number,Y:number,w:number,color:string)=>{c.strokeStyle=color;c.lineWidth=w;c.lineCap='round';c.beginPath();c.moveTo(x,y);c.lineTo(X,Y);c.stroke();};
 c.save();c.translate(FRAME/2,FOOT);ellipse(0,3,16,6,'#09121c66');if(seated){round(-11,-9,22,15,4,'#334653');round(-10,-body-5,20,17,4,'#506778');}
 line(-5,-body+5,-6+leg,-2,6,'#283847');line(5,-body+5,6-leg,-2,6,'#283847');round(-11+leg,-5,11,5,2,'#14212d');round(1-leg,-5,11,5,2,'#14212d');
 round(-13,-body-18-bob,26,29,7,'#203344');round(-11,-body-17-bob,22,26,6,coat);line(-4,-body-14-bob,0,-body-5-bob,3,'#e8e6df');line(4,-body-14-bob,0,-body-5-bob,3,'#e8e6df');round(4,-body-8-bob,5,6,1,'#e6f2ee');
 const hand=walking?leg*.65:f.clip==='work'||f.clip==='meeting'?phase*4:0;
 line(-10,-body-11-bob,-14+hand,-body+1,6,coat);line(10,-body-11-bob,14-hand,-body+1,6,coat);ellipse(-14+hand,-body+1,3.5,3.5,skin);ellipse(14-hand,-body+1,3.5,3.5,skin);
 round(-10,head-3,20,22,7,skin);ellipse(0,head,11,6.5,hair);round(-f.dir*7-3,head+1,6,11,2,hair);ellipse(f.dir*4,head+8,1.5,f.clip==='rest'&&f.index===1?.35:1.5,'#263545');ellipse(f.dir*8,head+8,1.2,f.clip==='rest'&&f.index===1?.35:1.2,'#263545');
 if(f.role==='engineer'){c.strokeStyle='#cedce6';c.lineWidth=1.4;c.strokeRect(-7,head+4,7,7);c.strokeRect(1,head+4,7,7);line(0,head+7,1,head+7,1,'#cedce6');}
 if(f.role==='orchestrator')line(0,-body-7-bob,0,-body+1-bob,2,'#d6b269');
 if(f.role==='research')round(-11,head+11,3,5,1,'#e7c685');
 if(f.role==='qa')round(6,-body-16-bob,5,5,2,'#e5d9bc');
 c.restore();
}
export function paintAtlas(c:CanvasRenderingContext2D){
 c.clearRect(0,0,atlasSize.w,atlasSize.h);
 for(const f of frames){c.save();c.translate(f.x,f.y);c.beginPath();c.rect(0,0,FRAME,FRAME);c.clip();paintAvatar(c,f);c.restore();}
}
