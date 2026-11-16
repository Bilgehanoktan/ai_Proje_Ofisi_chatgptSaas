"""Reproduce only the two reviewed product edits from exact P10G parent files."""
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1]); f=base/'product/ai-company-os-frontend'
def blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def once(s,old,new):
    if s.count(old)!=1: raise ValueError('Patch anchor mismatch: '+old[:80])
    return s.replace(old,new,1)
patches={
 'components/dashboard/OfficePanel.tsx':('539833649fa3de74dfe8e7a79f7bfe4fbec74dbb', [
 ('{!officeOnly&&<Link className="action-link" href="/office">Tam ekran ↗</Link>}', '{!officeOnly&&<Link className="action-link" href="/office">Tam ekran ↗</Link>}<Link className="action-link" href="/office/premium">Premium Studio · D0 ↗</Link>')]),
 'office/scenes/OfficeScene.tsx':('edc39bfc6814e1cff97233fc525dc04366f48866', [
 ("import {cameraView,iso,markerPosition,pointKey,route,type Floor,type Point} from '../engine/geometry';", "import {cameraView,iso,markerPosition,pointKey,route,type Floor,type Point} from '../engine/geometry';\nimport {inputPan,inputZoom,inputDragged} from '../engine/cameraInput';"),
 ('let elapsed=0,lastPlayId=-1;', '''let elapsed=0,lastPlayId=-1;
   // Local visual gesture state only; no placement or runtime state is emitted.
   const stationZones=new Map<import('phaser').GameObjects.GameObject,string>();
   const stationAt=(over:import('phaser').GameObjects.GameObject[])=>over.map(o=>stationZones.get(o)).find(id=>id!==undefined)??null;
   let drag:{id:number;sx:number;sy:number;lx:number;ly:number;moved:boolean;station:string|null}|null=null;'''),
 ("this.add.zone(cx,cy,76,55).setInteractive({useHandCursor:true}).on('pointerdown',()=>{if(!cancelled)setSelected(s.id);});", "const zone=this.add.zone(cx,cy,76,55).setInteractive({useHandCursor:true});stationZones.set(zone,s.id);"),
 ("if(!floor.stations.length)this.add.text(450,440,'GENİŞLEME REZERVİ'", '''// Phaser emits game-coordinate pointer positions; existing cameraView remains the clamp authority.
     this.input.on('pointerdown',(p:import('phaser').Input.Pointer,over:import('phaser').GameObjects.GameObject[])=>{
      if(!cancelled&&p.button===0&&!drag)drag={id:p.id,sx:p.x,sy:p.y,lx:p.x,ly:p.y,moved:false,station:stationAt(over)};
     });
     this.input.on('pointermove',(p:import('phaser').Input.Pointer)=>{
      if(cancelled||!drag||p.id!==drag.id||!p.isDown)return;
      if(!drag.moved&&!inputDragged(drag.sx,drag.sy,p.x,p.y))return;
      const dx=p.x-drag.lx,dy=p.y-drag.ly;drag.lx=p.x;drag.ly=p.y;drag.moved=true;setView(v=>inputPan(v,dx,dy));
     });
     this.input.on('pointerup',(p:import('phaser').Input.Pointer,over:import('phaser').GameObjects.GameObject[])=>{
      if(cancelled||!drag||p.id!==drag.id)return;
      if(!drag.moved&&!inputDragged(drag.sx,drag.sy,p.x,p.y)&&drag.station&&drag.station===stationAt(over))setSelected(drag.station);
      drag=null;
     });
     this.input.on('pointerupoutside',()=>{drag=null;});this.input.on('gameout',()=>{drag=null;});
     this.input.on('wheel',(p:import('phaser').Input.Pointer,_over:unknown, _dx:number,dy:number)=>{if(!cancelled&&!drag)setView(v=>inputZoom(v,p.x,p.y,dy));});
     if(!floor.stations.length)this.add.text(450,440,'GENİŞLEME REZERVİ' '''.rstrip()),
 ("<div className=\"engine-frame\">", "<p className=\"sub\">Fare sürükleme ve tekerlek · D0 görsel kamera; istasyon seçimi tıklama bırakıldığında yapılır.</p><div className=\"engine-frame\">")])}
pending=[]
for rel,(sha,changes) in patches.items():
    p=f/rel; b=p.read_bytes(); assert blob(b)==sha,f'Unexpected parent: {rel}'; text=b.decode();
    for old,new in changes: text=once(text,old,new)
    pending.append((p,text))
for p,text in pending:p.write_text(text,encoding='utf8',newline='\n')
