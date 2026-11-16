"""Standalone Chromium camera checks; no product execution."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os,json,math
root=Path(__file__).resolve().parent
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
html=(root/'office.html').read_text(encoding='utf-8')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
    errors=[];requests=[]
    def watch(pg):
        pg.on('pageerror',lambda e:errors.append(str(e)))
        pg.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
    watch(page);page.set_content(html);page.wait_for_timeout(150)
    ev=page.evaluate
    def state(): return ev('({zoom,cx,cy,floor,chosen,motionFollow,box:cameraLimit()})')
    def bounds(): return ev('(()=>{const v=cameraLimit();return (v.w>=1100?cx===550:v.x>=-1e-6&&v.x+v.w<=1100+1e-6)&&(v.h>=720?cy===360:v.y>=-1e-6&&v.y+v.h<=720+1e-6)})()')
    def pos():
        b=page.locator('#scene').bounding_box();return (b['x']+b['width']*.58,b['y']+b['height']*.52)
    check('four original avatars',page.locator('[data-avatar]').count()==4)
    check('four minimap markers',page.locator('#cameraMapActors circle').count()==4)
    check('initial viewport bounds',bounds())
    check('initial full world',state()['box']['w']>=1099.99 and state()['box']['h']>=719.99)
    x,y=pos();old=ev('([x,y])=>{const p=cameraPoint(scene,x,y);return [p.x,p.y]}',[x,y]);page.mouse.move(x,y);page.mouse.wheel(0,-260);page.wait_for_timeout(100)
    new=ev('([x,y])=>{const p=cameraPoint(scene,x,y);return [p.x,p.y]}',[x,y]);check('wheel zoom in',state()['zoom']>1.4);check('cursor anchor preserved',math.dist(old,new)<1.5)
    check('zoom bounds',bounds());prev=state();page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+70,y-35,steps=8);page.mouse.up();check('mouse drag moves camera',state()['cx']<prev['cx'] and state()['cy']>prev['cy']);check('drag clears pointer state',ev('cameraPointers.size===0&&!cameraDragged'));check('drag class removed',not page.locator('#scene').evaluate("el=>el.classList.contains('camera-drag')"))
    ev('zoom=2.4;cx=-9999;cy=9999;camera()');check('hard clamp both axes',bounds());check('no blank world at maximum zoom',state()['box']['x']>=-1e-6)
    page.locator('#reset').click();check('reset',state()['zoom']==1 and state()['cx']==550 and state()['cy']==360)
    page.locator('[data-cast=engineer]').click();check('agent selected',state()['chosen']=='engineer');check('selection auto focus',state()['zoom']==1.75);check('focus inside bounds',bounds());a=page.locator('[data-avatar=research]').bounding_box();ax=a['x']+a['width']/2;ay=a['y']+a['height']/2;page.mouse.move(ax,ay);page.mouse.down();page.mouse.move(ax+45,ay+12,steps=5);page.mouse.up();check('drag from avatar does not select',state()['chosen']=='engineer');page.locator('[data-cast=research]').click();check('ordinary selection after drag',state()['chosen']=='research')
    page.locator('#motionFollow').click();check('follow enabled',state()['motionFollow']);check('minimap follow mode',page.locator('#cameraMode').inner_text()=='TAKİP');page.locator('#motionPause').click();page.locator('#left').click();check('manual button cancels follow while paused',not state()['motionFollow'] and page.locator('#motionFollow').get_attribute('aria-pressed')=='false');page.locator('#motionPause').click();page.locator('#motionFollow').click()
    x,y=pos();page.mouse.move(x,y);page.mouse.wheel(0,-100);page.wait_for_timeout(60);check('wheel cancels follow',not state()['motionFollow']);check('follow button updated',page.locator('#motionFollow').get_attribute('aria-pressed')=='false')
    page.locator('#motionFollow').click();b=page.locator('#cameraMap').bounding_box();prev=state();page.mouse.click(b['x']+b['width']*.8,b['y']+b['height']*.65);check('minimap cancels follow',not state()['motionFollow']);check('minimap navigation',state()['cx']!=prev['cx']);check('minimap bounds',bounds())
    v=state()['box'];m=page.locator('#cameraMapViewport');check('map viewport x matches',abs(float(m.get_attribute('x'))-max(0,v['x']))<1e-6);check('map viewport width matches',abs(float(m.get_attribute('width'))-(min(1100,v['x']+v['w'])-max(0,v['x'])))<1e-6)
    page.locator('#cameraMap').focus();prev=state();page.keyboard.press('ArrowLeft');check('map keyboard pans',state()['cx']<prev['cx']);page.keyboard.press('Home');check('keyboard Home reset',state()['zoom']==1)
    page.locator('#scene').focus();page.keyboard.press('+');check('scene keyboard zoom',state()['zoom']>1);page.keyboard.press('Home');check('scene keyboard reset',state()['zoom']==1)
    page.locator('button[data-room=meeting]').click();check('room focus preserved',state()['zoom']==1.65);check('room selection preserved',ev("selected==='meeting'"))
    page.locator('[data-floor="2"]').click();check('floor transition active',page.locator('#scene').evaluate("el=>el.classList.contains('camera-floor-enter')"));check('passive floor no avatars',page.locator('[data-avatar]').count()==0);check('passive map no markers',page.locator('#cameraMapActors circle').count()==0);check('passive motion blocked',page.locator('[data-motion=work]').is_disabled());check('passive follow disabled',page.locator('#motionFollow').is_disabled());page.wait_for_timeout(400);check('floor animation completes',not page.locator('#scene').evaluate("el=>el.classList.contains('camera-floor-enter')"));page.screenshot(path=str(root/'Floor2.png'),full_page=True)
    page.locator('[data-floor="1"]').click();page.wait_for_timeout(400);check('return restores avatars',page.locator('[data-avatar]').count()==4);check('return restores map markers',page.locator('#cameraMapActors circle').count()==4)
    page.emulate_media(reduced_motion='reduce');page.locator('[data-floor="2"]').click();check('reduced motion no floor transition',not page.locator('#scene').evaluate("el=>el.classList.contains('camera-floor-enter')"));page.locator('[data-floor="1"]').click();page.locator('[data-cast=qa]').click();page.locator('[data-motion=work]').click();check('reduced motion still works',page.locator('[data-avatar=qa]').get_attribute('data-state')=='working');page.emulate_media(reduced_motion='no-preference')
    page.locator('#motionReset').click();page.locator('[data-cast=orch]').click();page.locator('[data-motion=meeting]').click();page.wait_for_timeout(150);before=ev("document.querySelector('#cameraMapActors circle').getAttribute('cx')");page.wait_for_timeout(200);after=ev("document.querySelector('#cameraMapActors circle').getAttribute('cx')");check('map actor marker updates during actual motion',before!=after);page.locator('#motionPause').click();page.locator('#reset').click();page.screenshot(path=str(root/'Office.png'),full_page=True)
    page.locator('[data-cast=engineer]').click();page.screenshot(path=str(root/'Focused.png'),full_page=True)
    # Actual touch input via Chromium DevTools touch events (emulated touchscreen).
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True);watch(mobile);mobile.set_content(html);mobile.wait_for_timeout(100)
    check('mobile no overflow',mobile.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('mobile initial full world',mobile.evaluate('cameraLimit().w>=1099.99&&cameraLimit().h>=719.99'))
    cdp=mobile.context.new_cdp_session(mobile);sb=mobile.locator('#scene').bounding_box();mx=sb['x']+sb['width']/2;my=sb['y']+sb['height']/2
    def touch(t,pts):cdp.send('Input.dispatchTouchEvent',{'type':t,'touchPoints':[{'x':x,'y':y,'id':i} for i,x,y in pts]})
    touch('touchStart',[(1,mx-25,my),(2,mx+25,my)]);touch('touchMove',[(1,mx-55,my),(2,mx+55,my)]);touch('touchEnd',[]);mobile.wait_for_timeout(120)
    check('touch pinch increases zoom',mobile.evaluate('zoom>1.5'));check('touch pinch ends cleanly',mobile.evaluate('cameraPointers.size===0'))
    prev=mobile.evaluate('cx');touch('touchStart',[(1,mx,my)]);touch('touchMove',[(1,mx+30,my)]);touch('touchMove',[(1,mx+60,my)]);touch('touchEnd',[]);mobile.wait_for_timeout(80);check('one finger touch drag',mobile.evaluate('cx')<prev);check('touch bounds',mobile.evaluate('(()=>{const v=cameraLimit();return v.x>=-1e-6&&v.x+v.w<=1100+1e-6})()'))
    mobile.locator('#reset').tap();mobile.wait_for_timeout(350);check('mobile reset tap',mobile.evaluate('zoom===1'));mobile.screenshot(path=str(root/'Mobile.png'),full_page=True)
    check('no JS errors',not errors);check('no external network',not requests)
    version=browser.version;browser.close()
(root/'TEST_EVIDENCE.json').write_text(json.dumps({'scope':'Standalone Chromium set_content, actual mouse/wheel and CDP touch events; not full product','chromium':version,'pass':len(checks),'checks':checks,'product_build':'NOT_RUN','phaser':'NOT_RUN'},indent=2)+'\n')
print(f'{len(checks)}/{len(checks)} PASS')
