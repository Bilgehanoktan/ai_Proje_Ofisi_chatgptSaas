"""Actual built local lifecycle UI; opt-in, not independent acceptance."""
import argparse
from playwright.sync_api import sync_playwright, expect
p=argparse.ArgumentParser()
p.add_argument('--chromium',required=True)
p.add_argument('--frontend-port',type=int,default=17300)
args=p.parse_args()
if not 1024<=args.frontend_port<=49151: raise ValueError('invalid frontend port')
origin=f'http://127.0.0.1:{args.frontend_port}'
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=args.chromium)
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[];external=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    def guard(route):
        url=route.request.url
        if url.startswith(origin+'/') or url.startswith('data:') or url.startswith('blob:'+origin+'/'): route.continue_()
        else: external.append(url);route.abort()
    page.route('**/*',guard)
    page.goto(origin+'/',wait_until='networkidle')
    page.get_by_role('group',name='CEO bölümleri seçimi').get_by_role('button',name='Teknik kanıtlar',exact=False).click()
    panel=page.get_by_role('region',name='CEO / LIFECYCLE')
    expect(panel).to_be_visible()
    read=panel.get_by_role('button',name='Lifecycle kaydını oku')
    read.click()
    expect(panel.get_by_role('status')).to_contain_text('Sabit tarihsel örnek eşleşti')
    expect(panel).to_contain_text('v5 · FAILED')
    expect(panel).to_contain_text('20 minor USD')
    page.route('**/api/demo/lifecycle',lambda r:r.fulfill(status=200,content_type='application/json',body='{"authoritative":true}'))
    read.click()
    expect(panel.get_by_role('status')).to_contain_text('Kayıt yok veya uyuşmuyor')
    expect(panel).not_to_contain_text('v5 · FAILED')
    page.unroute('**/api/demo/lifecycle')
    page.goto(origin+'/office',wait_until='networkidle')
    office=page.get_by_role('region',name='OFFICE / LIFECYCLE')
    expect(office.get_by_role('status')).to_contain_text('Okunmadı')
    office.get_by_role('button',name='Lifecycle kaydını oku').click()
    expect(office).to_contain_text('v5 · FAILED')
    assert not errors,errors
    assert not external,external
    browser.close()
print('PASS lifecycle readback, malformed response clears state, independent office read')
