"""Opt-in P03 browser check: historical prefix, malformed response, floor reset."""
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
    panel=page.get_by_role('region',name='ceo / historical prefix')
    read=panel.get_by_role('button',name='Görev örneğini oku')
    read.click()
    expect(panel.get_by_role('status')).to_contain_text('Tarihsel prefix eşleşti')
    expect(panel).to_contain_text('v3 · RUNNING')
    expect(panel).to_contain_text('UNKNOWN')
    page.route('**/api/demo/lifecycle-prefix',lambda r:r.fulfill(status=200,content_type='application/json',body='{"lease_freshness":"FRESH"}'))
    read.click()
    expect(panel.get_by_role('status')).to_contain_text('Kayıt yok veya uyuşmuyor')
    expect(panel).not_to_contain_text('v3 · RUNNING')
    page.unroute('**/api/demo/lifecycle-prefix')
    page.goto(origin+'/office',wait_until='networkidle')
    office=page.get_by_role('region',name='office / historical prefix')
    expect(office.get_by_role('status')).to_contain_text('Okunmadı')
    office.get_by_role('button',name='Görev örneğini oku').click()
    expect(office).to_contain_text('v3 · RUNNING')
    floors=page.get_by_role('group',name='Kat seçimi').get_by_role('button')
    floors.nth(1).click()
    expect(office.get_by_role('status')).to_contain_text('Okunmadı')
    expect(office).not_to_contain_text('v3 · RUNNING')
    assert not errors,errors
    assert not external,external
    browser.close()
print('PASS historical prefix, wrong freshness rejected, floor reset')
