"""Actual Chromium execution of compiled pure helpers. Not a Phaser/Next E2E."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]); fixture=json.loads(Path(sys.argv[2]).read_text())
modules=['premiumRouting','premiumTraffic','premiumModel','premiumOfficeV0']
script='const modules={},cache={};\n'+ '\n'.join('modules["./'+n+'"]=(module,exports,require)=>{\n'+(root/(n+'.js')).read_text()+'\n};' for n in modules)+'''\nfunction req(n){if(!cache[n]){const m={exports:{}};cache[n]=m;modules[n](m,m.exports,req);}return cache[n].exports;}window.M=req('./premiumModel');window.V=req('./premiumOfficeV0');'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content('<main>Pure D0 model diagnostic; no Phaser.</main>');page.add_script_tag(content=script)
 results=page.evaluate('''fixture=>{const check=(condition,name)=>{if(!condition)throw Error(name);return name};const out=[];
 const invariant=a=>{const cells=[];for(const v of a){if(!M.walkable(v.cell))throw Error('blocked cell');cells.push(v.cell.join(','));if(v.progress>0){if(!M.walkable(v.path[0]))throw Error('blocked destination');cells.push(v.path[0].join(','));}}if(new Set(cells).size!==cells.length)throw Error('collision');};
 const goals=[[8,2],[9,2],[10,2],[10,1]];
 for(const n of [3,4]){const a=M.initialActors();a.slice(0,n).forEach((v,i)=>{v.cell=goals[(i+1)%n];M.command(a,v.role,'meeting');});let planned=false;for(let i=0;i<800;i++){M.advance(a,.1);invariant(a);planned ||= M.routeStatus(a)==='TRAFFIC_PLANNING';}out.push(check(planned&&a.slice(0,n).every((v,i)=>v.cell.join(',')===goals[i].join(',')&&v.mode==='meeting'),n+' actor cycle'));}
 const g=V.inspectGeometryGap(fixture,M.initialActors());out.push(check(g.rows.length===4&&!g.placement&&g.status==='JOIN_HOLD','historical geometry held'));out.push(check(V.inspectGeometryGap({...fixture,wa_epoch:9},M.initialActors()).rows.length===0,'forged epoch rejected'));
 return out;}''',fixture);assert not errors,errors
 print('Chromium',b.version);print('\n'.join('PASS '+x for x in results));print(f'{len(results)}/{len(results)} PASS (pure browser model only)');b.close()
