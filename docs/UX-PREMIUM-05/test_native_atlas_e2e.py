"""Prepared native acceptance extension; NOT_RUN here. Exact local Next checkout required."""
import sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect
base=sys.argv[1].rstrip('/');u=urlsplit(base);assert u.scheme=='http' and u.hostname in ('127.0.0.1','localhost')
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1440,'height':960},reduced_motion='no-preference');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/office/premium/native');expect(page.locator('canvas')).to_be_visible(timeout=15000);expect(page.locator('[data-asset-mode]')).to_have_attribute('data-asset-mode','atlas',timeout=15000)
 page.get_by_role('button',name='engineer',exact=True).click();page.get_by_role('button',name='Toplantı',exact=True).click();expect(page.locator('[data-visual-role=engineer]')).to_have_attribute('data-visual-mode','meeting',timeout=30000)
 page.get_by_role('button',name='Kat 2 · Rezerv',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(0)
 page.get_by_role('button',name='Kat 1',exact=True).click();expect(page.locator('[data-visual-role]')).to_have_count(4)
 page.emulate_media(reduced_motion='reduce');expect(page.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled()
 page.reload();expect(page.locator('[data-asset-mode]')).to_have_attribute('data-asset-mode','atlas',timeout=15000);assert not errors,errors;b.close()
print('Native atlas smoke PASS; manual occlusion/visual review still required')
