"""Actual React task-budget acceptance; requires isolated, built local product."""
import argparse
from playwright.sync_api import sync_playwright, expect

p=argparse.ArgumentParser();p.add_argument('--chromium',required=True);p.add_argument('--frontend-port',type=int,default=3000);args=p.parse_args()
if not 1024 <= args.frontend_port <= 49151: raise ValueError('invalid frontend port')
origin=f'http://127.0.0.1:{args.frontend_port}'
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=args.chromium)
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[];external=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    def guard(route):
        url=route.request.url
        if url.startswith(origin+'/') or url.startswith('data:') or url.startswith('blob:'+origin+'/'):route.continue_()
        else:external.append(url);route.abort()
    page.route('**/*',guard)
    page.goto(origin+'/',wait_until='networkidle')
    page.get_by_role('group',name='CEO bölümleri seçimi').get_by_role('button',name='Operasyonlar',exact=False).click()
    panel=page.get_by_role('region',name='Ortak görev ve bütçe örneği')
    expect(panel).to_be_visible()
    read=panel.get_by_role('button',name='Ortak kayıt oku')
    read.click();expect(panel.get_by_role('status')).to_contain_text('DENY')
    expect(panel).to_contain_text('UNKNOWN_HOLD');expect(panel).to_contain_text('100 / 900')
    expect(panel).to_contain_text('Nedensellik kanıtlanmadı')
    page.route('**/api/demo/task-budget',lambda r:r.fulfill(status=200,content_type='application/json',body='{"spend_allowed":true}'))
    read.click();expect(panel.get_by_role('status')).to_contain_text('HOLD')
    expect(panel).not_to_contain_text('UNKNOWN_HOLD')
    page.unroute('**/api/demo/task-budget')
    floors=page.get_by_role('group',name='Kat seçimi').get_by_role('button')
    floors.nth(1).click();expect(panel).to_have_count(0)
    floors.nth(0).click();expect(panel.get_by_role('status')).to_contain_text('Henüz okunmadı')
    assert not errors,errors;assert not external,external
    browser.close()
print('PASS actual paired panel, malformed response HOLD, reserve floor reset')
