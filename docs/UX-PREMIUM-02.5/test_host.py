"""Chromium srcdoc sandbox diagnostic of route-derived HTML; not actual Next routing."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,os,html
root=Path(__file__).resolve().parent
asset=root/'source/product/ai-company-os-frontend/office/assets/premiumOfficeHtml.ts'
checks=[]
def check(n,v):
    assert v,n
    checks.append(n)
import hashlib
from html.parser import HTMLParser
class FrameParser(HTMLParser):
    def handle_starttag(self,tag,attrs):
        if tag=='iframe': self.attrs=dict(attrs)
source=(root/'host.html').read_text(); parser=FrameParser();parser.feed(source)
check('route embeds exact 02.4 bytes',hashlib.sha256(parser.attrs['srcdoc'].encode()).hexdigest()=='05c1af2f387131bbebd149de5c9bbe53b687a404c1e24d19aec32e0da5d13e6d');check('no public asset URL', 'src' not in parser.attrs)
diagnostic=source
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 errors=[];urls=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:urls.append(r.url));page.set_content(diagnostic,wait_until='load');frame=page.frames[1]
 iframe=page.locator('iframe');check('title',iframe.get_attribute('title')=='Premium ofis görsel prototipi');check('sandbox exactly scripts',iframe.get_attribute('sandbox')=='allow-scripts');check('no referrer',iframe.get_attribute('referrerpolicy')=='no-referrer');check('back link',page.get_by_text('← Mevcut ofis / Phaser').get_attribute('href')=='/office');check('explicit HOLD', 'JOIN_HOLD' in page.locator('[role=status]').inner_text());check('4 decorative avatars',frame.locator('[data-avatar]').count()==4)
 check('opaque security origin',frame.evaluate('self.origin')=='null');check('parent DOM denied',frame.evaluate("(()=>{try{void parent.document;return false}catch(e){return e.name==='SecurityError'}})()"));check('storage denied',frame.evaluate("(()=>{try{localStorage.getItem('x');return false}catch(e){return e.name==='SecurityError'}})()"));check('parent cannot read frame DOM',page.evaluate("document.querySelector('iframe').contentDocument===null"));check('connect-src blocks data fetch',frame.evaluate("async()=>{try{await fetch('data:text/plain,probe');return false}catch(e){return true}}"))
 frame.locator('[data-cast=engineer]').click();check('role focus',frame.evaluate("chosen==='engineer'&&zoom===1.75"));frame.locator('[data-motion=work]').click();check('visual action',frame.locator('[data-avatar=engineer]').count()==1);frame.locator('[data-floor="2"]').click();check('reserve floor empty',frame.locator('[data-avatar]').count()==0);check('reserve markers empty',frame.locator('#cameraMapActors circle').count()==0);check('reserve action disabled',frame.locator('[data-motion=work]').is_disabled());frame.locator('[data-floor="1"]').click();check('restore avatars',frame.locator('[data-avatar]').count()==4);check('no HTTP requests',not [u for u in urls if u.startswith(('http:','https:'))]);check('no JS errors',not errors);frame.locator('#reset').click();page.screenshot(path=str(root/'Integrated_Host.png'),full_page=True)
 mobile=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True);mobile.set_content(diagnostic,wait_until='load');mf=mobile.frames[1];check('mobile host no horizontal overflow',mobile.evaluate('document.documentElement.scrollWidth<=innerWidth'));check('mobile iframe no overflow',mf.evaluate('document.documentElement.scrollWidth<=innerWidth'));mf.locator('[data-floor="2"]').tap();mobile.wait_for_timeout(400);tap_ok=mf.locator('[data-avatar]').count()==0; residuals=[] if tap_ok else ['embedded iframe touch tap did not activate floor control'];
 if not tap_ok: mf.locator('[data-floor="2"]').click()
 check('mobile floor via click fallback',mf.locator('[data-avatar]').count()==0);mf.locator('[data-floor="1"]').click();mobile.wait_for_timeout(400);mobile.screenshot(path=str(root/'Mobile_Host.png'),full_page=True);version=b.version;b.close()
(root/'BROWSER_EVIDENCE.json').write_text(json.dumps({'scope':'Chromium set_content, route-derived static JSX diagnostic with exact srcdoc; actual Next/React/Phaser NOT_RUN','chromium':version,'checks':checks,'pass':len(checks),'residuals':residuals,'touch_tap_pass':tap_ok,'http_navigation':'BLOCKED_BY_ADMINISTRATOR','full_product':'NOT_RUN'},ensure_ascii=False,indent=2)+'\n')
print(f'{len(checks)}/{len(checks)} PASS')
