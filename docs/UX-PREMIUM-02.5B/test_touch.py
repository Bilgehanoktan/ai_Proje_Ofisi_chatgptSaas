from pathlib import Path
from playwright.sync_api import sync_playwright
import json,os,html,hashlib
root=Path(__file__).resolve().parent
from pathlib import Path
import sys
front=Path(sys.argv[1]) if len(sys.argv)>1 else root/'source/product/ai-company-os-frontend'
raw=(front/'office/assets/premiumOfficeHtml.ts').read_text().split('export const premiumOfficeHtml = ',1)[1].strip().removesuffix(';')
fixed=json.loads(raw);patch='<script>\n'+(root/'touch_fix.js').read_text()+'</script>'
assert fixed.count(patch)==1
old=fixed.replace(patch,'',1)
assert hashlib.sha256(old.encode()).hexdigest()=='05c1af2f387131bbebd149de5c9bbe53b687a404c1e24d19aec32e0da5d13e6d'
shell=(root/'host_shell.html').read_text()
source=shell.replace('__SRC_DOC__',html.escape(fixed,quote=True));prior=shell.replace('__SRC_DOC__',html.escape(old,quote=True));checks=[]
def check(n,v):
 assert v,n
 checks.append(n)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 m=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
 m.set_content(prior,wait_until='load');f=m.frames[1];f.locator('[data-floor="2"]').tap();m.wait_for_timeout(350);before=f.evaluate('floor');print('parent tap floor',before)
 m.set_content(source,wait_until='load');f=m.frames[1];errors=[];m.on('pageerror',lambda e:errors.append(str(e)))
 check('sandbox preserved',m.locator('iframe').get_attribute('sandbox')=='allow-scripts');check('opaque origin',f.evaluate('self.origin')=='null')
 check('parent DOM denied',f.evaluate("(()=>{try{void parent.document;return false}catch(e){return e.name==='SecurityError'}})()"));check('connect-src blocks network',f.evaluate("async()=>{try{await fetch('data:text/plain,probe');return false}catch(e){return true}}"))
 f.locator('[data-floor="2"]').tap();m.wait_for_timeout(350);check('trusted touch selects floor 2',f.evaluate('floor')==2);check('reserve no actors',f.locator('[data-avatar]').count()==0);check('reserve no map markers',f.locator('#cameraMapActors circle').count()==0);check('reserve actions disabled',f.locator('[data-motion=work]').is_disabled())
 f.locator('[data-floor="1"]').tap();m.wait_for_timeout(350);check('trusted touch selects floor 1',f.evaluate('floor')==1);check('four roles restored',f.locator('[data-avatar]').count()==4)
 # movement > threshold must not select a floor: real CDP touch input, not dispatchEvent.
 el=f.locator('[data-floor="2"]');rect=el.bounding_box();x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2;cdp=m.context.new_cdp_session(m)
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+35,'y':y+30}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(400);check('drag does not activate floor',f.evaluate('floor')==1)
 check('mobile no horizontal overflow',m.evaluate('document.documentElement.scrollWidth<=innerWidth'));check('no page errors',not errors);m.screenshot(path=str(root/'Mobile_Touch.png'),full_page=True)
 d=b.new_page(viewport={'width':1440,'height':1000});d.set_content(source,wait_until='load');df=d.frames[1];df.locator('[data-floor="2"]').click();check('desktop mouse floor 2',df.evaluate('floor')==2);df.locator('[data-floor="1"]').focus();df.locator('[data-floor="1"]').press('Enter');check('keyboard floor 1',df.evaluate('floor')==1);df.locator('[data-cast=engineer]').click();check('role focus retained',df.evaluate("chosen==='engineer'"));df.locator('[data-motion=work]').click();check('motion command retained',df.locator('[data-avatar=engineer]').count()==1);d.screenshot(path=str(root/'Desktop_Touch.png'),full_page=True);version=b.version;b.close()
(root/'TOUCH_EVIDENCE.json').write_text(json.dumps({'scope':'Chromium set_content diagnostic host; actual Next not run','chromium':version,'parent_floor_after_tap':before,'checks':checks,'pass':len(checks),'physical_device':'NOT_RUN'},indent=2)+'\n');print(f'{len(checks)}/{len(checks)} PASS')
