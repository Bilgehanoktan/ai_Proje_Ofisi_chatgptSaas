from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
    errors=[]; network=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http:','https:')) else None)
    page.set_content((root/'office.html').read_text(encoding='utf-8'))
    check('four distinct roles',page.locator('[data-cast]').count()==4)
    check('four scene avatars',page.locator('[data-avatar]').count()==4)
    check('initial selected role',page.locator('[data-cast=orch]').get_attribute('aria-pressed')=='true')
    check('initial standing',page.locator('[data-avatar=orch]').get_attribute('data-pose')=='standing')
    page.locator('[data-cast=engineer]').click()
    check('select Engineer',page.locator('[data-cast=engineer]').get_attribute('aria-pressed')=='true')
    check('focus preserved',page.evaluate('document.activeElement.dataset.cast')=='engineer')
    page.locator('[data-pose-choice=seated]').click()
    check('seated SVG pose',page.locator('[data-avatar=engineer]').get_attribute('data-pose')=='seated')
    check('other role unchanged',page.locator('[data-avatar=qa]').get_attribute('data-pose')=='standing')
    check('pose aria',page.locator('[data-pose-choice=seated]').get_attribute('aria-pressed')=='true')
    check('decorative label', 'D0 / HOLD' in page.locator('.cast-note').inner_text())
    page.locator('[data-avatar=research]').focus();page.keyboard.press('Enter')
    check('keyboard scene selection',page.locator('[data-cast=research]').get_attribute('aria-pressed')=='true')
    page.locator('[data-floor="2"]').click()
    check('inactive floor no avatars',page.locator('[data-avatar]').count()==0)
    check('inactive floor text','pasif' in page.locator('.cast-note').inner_text())
    page.locator('[data-floor="1"]').click()
    check('restore four avatars',page.locator('[data-avatar]').count()==4)
    page.locator('#plus').click();check('parent zoom retained',page.locator('#reset').inner_text()=='120%')
    page.locator('#reset').click();check('parent reset retained',page.locator('#reset').inner_text()=='100%')
    page.locator('button[data-room=ceo]').click();check('parent room focus retained',page.locator('#reset').inner_text()=='165%')
    page.locator('#reset').click();page.locator('[data-cast=orch]').click();page.locator('[data-pose-choice=standing]').click()
    page.screenshot(path=str(root/'Office.png'),full_page=True)
    page.locator('#castPanel').screenshot(path=str(root/'Characters.png'))
    page.locator('[data-pose-choice=seated]').click();page.locator('#castPanel').screenshot(path=str(root/'Seated.png'))
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/'Mobile.png'),full_page=True)
    check('mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no JS errors',not errors);check('no external network',not network)
    version=browser.version;browser.close()
(root/'TEST_EVIDENCE.json').write_text(json.dumps({'scope':'standalone Chromium set_content, not product','chromium':version,'pass':len(checks),'checks':checks,'product_build':'NOT_RUN','phaser':'NOT_RUN'},indent=2)+'\n')
print(f'{len(checks)}/{len(checks)} PASS')
