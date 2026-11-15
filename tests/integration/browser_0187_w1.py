"""Actual Next product smoke + screenshot baseline, run only after pinned build.
Requires isolated loopback product on port 3000. No independent acceptance.
"""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
parser=argparse.ArgumentParser()
parser.add_argument('--chromium')
parser.add_argument('--output', required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
nav_items=json.loads((root/'product/ai-company-os-frontend/features/uiCatalog.json').read_text(encoding='utf-8'))['nav']
output=Path(args.output); output.mkdir(parents=True, exist_ok=True)
origin='http://127.0.0.1:3000'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.chromium)
    for width,height in [(1440,900),(390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height}, reduced_motion='reduce')
        errors=[]; external=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        def route_local(route):
            url=route.request.url
            if url.startswith(origin+'/') or url.startswith('data:') or url.startswith('blob:'+origin+'/'): route.continue_()
            else: external.append(url);route.abort()
        page.route('**/*',route_local)
        for theme in ['dark','light']:
            for index,(name,_) in enumerate(nav_items):
                page.goto(origin+'/',wait_until='networkidle')
                nav=page.get_by_role('navigation',name='Ana navigasyon')
                expect(nav.locator('button,a')).to_have_count(13)
                if name=='Sanal Ofis':
                    nav.get_by_role('link',name=name,exact=True).click(); expect(page).to_have_url(origin+'/office')
                elif name!='Genel Bakış': nav.get_by_role('button',name=name,exact=True).click()
                expect(page.locator('h1')).to_have_text('CEO Command Center' if name=='Genel Bakış' else name)
                if theme=='light':page.get_by_role('button',name='Açık tema').click()
                expect(page.locator('.eds-frame')).to_have_attribute('data-eds-theme',theme)
                if name in ('Genel Bakış','Sanal Ofis'):
                    office=page.get_by_role('region',name='Sanal ofis',exact=True)
                    expect(office.get_by_role('region',name='Görsel ofis kamerası')).to_be_visible()
                    expect(office.get_by_role('region',name='İstasyon görev gözlemleri')).to_be_visible()
                    expect(office).to_contain_text('JOIN_HOLD')
                    if name=='Genel Bakış':expect(page.get_by_role('region',name='Sentetik admission ve bütçe')).to_be_visible()
                if name=='İş ve Denetim':expect(page.get_by_role('region',name='Proje yönetim merkezi')).to_be_visible()
                if name=='SaaS ve Finans':expect(page.get_by_role('region',name='Finans ve SaaS merkezi')).to_be_visible()
                if name in ('Güvenlik','Raporlar'):expect(page.get_by_role('region',name='Güvenlik ve kanıt merkezi')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,width,theme)
                page.screenshot(path=str(output/f'{width}-{theme}-{index:02}.png'),full_page=True,animations='disabled')
        assert not errors,errors;assert not external,external;page.close()
    browser.close()
print('PASS 52 screen baseline captures; pixel comparison against reviewed baseline remains separate')
