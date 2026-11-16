"""Prepared only: real pinned Next/Phaser browser run remains NOT_RUN.
Run against approved local isolated server. No live backend/provider/credentials.
"""
import json,sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
base=sys.argv[1].rstrip('/');u=urlsplit(base);assert u.scheme=='http' and u.hostname in ('127.0.0.1','localhost')
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1440,'height':960},reduced_motion='no-preference');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/office/premium/native');canvas=page.locator('canvas');expect(canvas).to_be_visible(timeout=15000);expect(page.get_by_text('D0 · JOIN_HOLD · Dekoratif',exact=False)).to_contain_text('ready');expect(page.get_by_text('Snapshot: EXACT_HISTORICAL_SAMPLE',exact=False)).to_be_visible()
 view=page.locator('[data-camera-view]');page.get_by_role('button',name='+',exact=True).click();page.wait_for_function('JSON.parse(document.querySelector("[data-camera-view]").dataset.cameraView).zoom > 1');before=json.loads(view.get_attribute('data-camera-view'))
 bounds=canvas.bounding_box();assert bounds
 # click near top-left of mini camera in canvas logical coordinates, not CSS pixels
 page.mouse.click(bounds['x']+bounds['width']*875/1100,bounds['y']+bounds['height']*42/720)
 page.wait_for_function('(old)=>{let v=JSON.parse(document.querySelector("[data-camera-view]").dataset.cameraView);return Math.abs(v.x-old.x)>2||Math.abs(v.y-old.y)>2}',arg=before)
 page.get_by_role('button',name='engineer',exact=True).click();page.get_by_role('button',name='Çalışma',exact=True).click();actor=page.locator('[data-visual-role=engineer]');expect(actor).to_have_attribute('data-visual-mode','work',timeout=10000)
 page.get_by_role('button',name='Toplantı',exact=True).click();expect(actor).to_have_attribute('data-visual-moving','true',timeout=5000);expect(actor).to_have_attribute('data-visual-mode','meeting',timeout=30000)
 page.get_by_role('button',name='Kat 2 · Rezerv',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(0);expect(page.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled();page.get_by_role('button',name='Kat 1',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(4)
 page.get_by_role('button',name='Karakterleri sıfırla').click();expect(actor).to_have_attribute('data-visual-mode','idle');assert not errors,errors
 page.screenshot(path='premium-native-evidence.png');b.close()
print('Native route smoke PASS; visual depth/occlusion inspection remains separate')
