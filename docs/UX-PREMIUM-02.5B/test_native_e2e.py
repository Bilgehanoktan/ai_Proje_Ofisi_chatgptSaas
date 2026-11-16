"""Prepared, NOT_RUN in this environment. Requires reviewed pinned Next dev server.
Usage: python test_native_e2e.py http://127.0.0.1:3000
No backend/provider/real agents required or authorized.
"""
import sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
base=sys.argv[1].rstrip('/');u=urlsplit(base);assert u.scheme=='http' and u.hostname in ('127.0.0.1','localhost')
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1440,'height':960},reduced_motion='no-preference');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/office/premium/native');expect(page.locator('canvas')).to_be_visible(timeout=15000);expect(page.get_by_text('D0 · JOIN_HOLD',exact=False)).to_contain_text('ready');
 page.get_by_role('button',name='engineer',exact=True).click();page.get_by_role('button',name='Çalışma',exact=True).click();actor=page.locator('[data-visual-role=engineer]');expect(actor).to_have_attribute('data-visual-mode','work',timeout=10000)
 page.get_by_role('button',name='Toplantı',exact=True).click();expect(actor).to_have_attribute('data-visual-moving','true',timeout=5000);expect(actor).to_have_attribute('data-visual-mode','meeting',timeout=30000)
 page.get_by_role('button',name='Kat 2 · Rezerv',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(0);expect(page.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled();page.get_by_role('button',name='Kat 1',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(4)
 page.get_by_role('button',name='Karakterleri sıfırla').click();expect(actor).to_have_attribute('data-visual-mode','idle');assert not errors,errors
 # Real renderer camera/pinch/occlusion require additional visual acceptance; no assertion by source syntax.
 b.close()
print('Native route smoke PASS')
