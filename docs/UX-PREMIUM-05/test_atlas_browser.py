"""Real Chromium Canvas atlas test; no Phaser or Next runtime. Optional atlas PNG output."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]); modules=['engine/premiumTraffic','engine/premiumModel','engine/premiumPresentation','scenes/premiumAtlasPaint','engine/premiumLift']
script='const modules={},cache={};\n'+'\n'.join('modules["'+n+'"]=(module,exports,require)=>{\n'+(root/(n+'.js')).read_text()+'\n};' for n in modules)+'''
function load(n){if(!cache[n]){const m={exports:{}};cache[n]=m;modules[n](m,m.exports,p=>{const a=n.split('/');a.pop();for(const x of p.split('/')){if(x==='..')a.pop();else if(x!=='.')a.push(x);}return load(a.join('/'));});}return cache[n].exports;}
window.P=load('engine/premiumPresentation');window.A=load('scenes/premiumAtlasPaint');window.L=load('engine/premiumLift');'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content('<canvas id="atlas"></canvas>');page.add_script_tag(content=script)
 result=page.evaluate('''()=>{const c=document.querySelector('canvas');c.width=P.atlasSize.w;c.height=P.atlasSize.h;const x=c.getContext('2d',{willReadFrequently:true});A.paintAtlas(x);const out=[];const check=(v,n)=>{if(!v)throw Error(n);out.push(n)};const data=f=>x.getImageData(f.x,f.y,P.FRAME,P.FRAME).data;
 check(P.frames.every(f=>{const a=data(f);return a.some((v,i)=>i%4===3&&v>200)}),'176 nonempty pixel frames');
 check(P.frames.every(f=>{const a=data(f),w=P.FRAME;for(let i=0;i<w;i++)for(const j of [i*4+3,((w-1)*w+i)*4+3,(i*w)*4+3,(i*w+w-1)*4+3])if(a[j])return false;return true}),'transparent frame edges / no bleed');
 const find=(r,d,clip,i)=>P.frames.find(f=>f.role===r&&f.dir===d&&f.clip===clip&&f.index===i);const diff=(a,b)=>data(a).some((v,i)=>v!==data(b)[i]);
 check(diff(find('engineer',1,'walk',0),find('engineer',1,'walk',2)),'walking motion pixel difference');
 check(diff(find('engineer',-1,'work',0),find('engineer',1,'work',0)),'direction pixel difference');
 check(diff(find('orchestrator',1,'idle',0),find('qa',1,'idle',0)),'role pixel difference');
 const first=c.toDataURL();A.paintAtlas(x);check(c.toDataURL()===first,'repeat paint deterministic');
 const l=L.initialLift();L.enqueueLift(l,{role:'qa',from:1,to:2});for(let i=0;i<40;i++)L.tickLift(l,.25,()=>false);check(l.phase==='exit'&&l.active.role==='qa','lift blocked landing held in browser');return out;}''');assert not errors,errors
 print('Chromium',b.version);print('\n'.join('PASS '+n for n in result));print(f'{len(result)}/{len(result)} PASS (Canvas + pure lift; not Phaser)')
 if len(sys.argv)>2: Path(sys.argv[2]).write_bytes(__import__('base64').b64decode(page.evaluate("document.querySelector('canvas').toDataURL().split(',')[1]")))
 b.close()
