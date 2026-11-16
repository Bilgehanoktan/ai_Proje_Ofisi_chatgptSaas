from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os
root=Path(__file__).resolve().parent
checks=[]
def check(name, value):
    checks.append({'name':name,'pass':bool(value)})
    assert value,name
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':960},device_scale_factor=1)
    errors=[]; network=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http:','https:')) else None)
    page.set_content((root/'office.html').read_text())
    check('four floor-1 rooms',page.locator('svg [data-room]').count()==4)
    check('detailed geometry',page.locator('svg polygon').count()>250)
    check('D0 label visible','HOLD' in page.locator('header').inner_text())
    page.screenshot(path=str(root/'Office.png'),full_page=True)
    page.locator('button[data-room=ceo]').click()
    check('CEO camera focus',page.locator('#reset').inner_text()=='165%' and 'CEO ofisi' in page.locator('#detail').inner_text())
    page.screenshot(path=str(root/'CEO_Room.png'),full_page=True)
    page.locator('button[data-room=meeting]').click()
    check('meeting focus','Strateji salonu' in page.locator('#detail').inner_text())
    page.screenshot(path=str(root/'Meeting_Room.png'),full_page=True)
    before=page.locator('#scene').get_attribute('viewBox');page.locator('#right').click()
    check('camera pan',before!=page.locator('#scene').get_attribute('viewBox'))
    page.locator('#reset').click();check('reset camera',page.locator('#scene').get_attribute('viewBox')=='0 0 1100 720')
    page.locator('#plus').click();check('zoom',page.locator('#reset').inner_text()=='120%')
    for _ in range(10):page.locator('#plus').click()
    check('zoom clamp',page.locator('#reset').inner_text()=='240%')
    page.locator('[data-floor="2"]').click();check('inactive floor no selectable rooms',page.locator('[data-room]').count()==0 and 'PASİF' in page.locator('#scene').text_content())
    check('floor camera reset',page.locator('#reset').inner_text()=='100%')
    page.locator('[data-floor="1"]').click();check('floor return',page.locator('svg [data-room]').count()==4)
    page.locator('svg [data-room=qa]').focus();page.keyboard.press('Enter');check('keyboard room focus','Kalite' in page.locator('#detail').inner_text())
    page.locator('#reset').click();page.set_viewport_size({'width':390,'height':844})
    check('mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    page.screenshot(path=str(root/'Mobile.png'),full_page=True)
    check('no JS runtime errors',not errors);check('no external HTTP',not network)
    browser.close()
(root/'TEST_EVIDENCE.json').write_text(json.dumps({'scope':'Standalone Chromium via set_content; not product acceptance','checks':checks,'passed':len(checks),'total':len(checks)},ensure_ascii=False,indent=2)+'\n')
print(f'{len(checks)}/{len(checks)} PASS')
