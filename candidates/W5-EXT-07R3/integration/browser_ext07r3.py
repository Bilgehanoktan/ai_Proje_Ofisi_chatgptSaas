"""EXT-06 actual product browser extension; run only with reviewed W8 stage."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def run(port, chromium, output):
    if not 1024 <= port <= 49151 or not chromium.is_file():
        raise ValueError('EXT07R3_BROWSER_SCOPE_HOLD')
    output.mkdir(parents=True, exist_ok=False)
    origin = f'http://127.0.0.1:{port}'
    blocked, errors, cases = [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(chromium))
        context = browser.new_context(viewport={'width':1440,'height':900}, reduced_motion='reduce', service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        def local(route):
            req=route.request
            if req.method in ('GET','HEAD') and (req.url.startswith(origin+'/') or req.url.startswith(('data:', 'blob:'+origin+'/'))):
                route.continue_()
            else:
                blocked.append({'method':req.method,'url':req.url.split('?')[0]});route.abort()
        context.route('**/*', local)
        page.goto(origin+'/', wait_until='networkidle')
        nav=page.get_by_role('navigation', name='Ana navigasyon')
        nav.get_by_role('button',name='Beceriler',exact=True).click()
        studio=page.get_by_role('region', name='Model, beceri ve hafıza incelemesi')
        catalog=studio.get_by_role('region', name='Harici yetenek kaynak kataloğu')
        cards=catalog.get_by_role('button',name='Kaynak ve kanıtı incele')
        role=catalog.get_by_label('Ajan rol şablonu')
        dept=catalog.get_by_label('Departman')
        search=catalog.get_by_label('Yetenek ara')
        detail=catalog.get_by_role('region',name='Harici yetenek kaynak denetçisi')
        expect(cards).to_have_count(3)
        for name in ('Superpowers','UI/UX Pro Max','Watch'):
            expect(catalog.get_by_role('heading',name=name,exact=True)).to_be_visible()
        expect(catalog).to_contain_text('QUARANTINED · DENY')
        expect(catalog).to_contain_text('bilinmiyor')
        cases.append('catalog-3-no-live-authority')
        role.select_option('research');expect(cards).to_have_count(2)
        dept.select_option('Araştırma');expect(cards).to_have_count(2)
        role.select_option('engineer');expect(cards).to_have_count(0)
        expect(catalog.get_by_text('Bu rol/departman ve arama için kaynak adayı yok.')).to_be_visible()
        cases.append('same-role-department-intersection')
        catalog.get_by_role('button',name='Filtreleri temizle').click()
        search.fill('watch');expect(cards).to_have_count(1)
        cards.first.click();expect(detail).to_contain_text('85855a5c4278c061ec0d0a63916ad7668a998e30')
        expect(detail).to_contain_text('G7 / G8');expect(detail).to_contain_text('Yok · HOLD')
        cases.append('search-selection-pinned-detail')
        page.screenshot(path=str(output/'01-dark-detail.png'),full_page=True)
        search.fill('no-match-ext07');expect(cards).to_have_count(0);expect(detail).to_have_count(0)
        studio.get_by_role('button',name='Temizle',exact=True).click()
        expect(cards).to_have_count(3);expect(search).to_have_value('');expect(role).to_have_value('all');expect(dept).to_have_value('all')
        cases.append('selection-reset-and-parent-clear')
        page.get_by_role('button',name='Açık tema').click()
        expect(page.locator('.eds-frame')).to_have_attribute('data-eds-theme','light')
        page.screenshot(path=str(output/'02-light.png'),full_page=True)
        cases.append('light-theme')
        page.set_viewport_size({'width':390,'height':844})
        expect(catalog).to_be_visible()
        assert catalog.evaluate('(e) => e.scrollWidth <= e.clientWidth + 1'), 'catalog horizontal overflow'
        role.focus();expect(role).to_be_focused();page.keyboard.press('Tab');expect(dept).to_be_focused()
        expect(catalog.get_by_role('button',name='Filtreleri temizle')).to_be_visible()
        page.screenshot(path=str(output/'03-mobile.png'),full_page=True)
        cases.append('mobile-catalog-overflow-keyboard')
        allowed={'Filtreleri temizle','Kaynak ve kanıtı incele','Kapat'}
        assert set(catalog.get_by_role('button').all_text_contents()) <= allowed, 'unexpected capability action'
        assert not blocked and not errors, (blocked,errors)
        cases.append('no-mutation-external-request-or-pageerror')
        browser.close()
    report={'status':'PASS','cases':cases,'screenshots':3,'actual_browser':True,'independent_acceptance':'HOLD'}
    (output/'EXT07R3_BROWSER_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frontend-port',required=True,type=int);p.add_argument('--chromium',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.frontend_port,a.chromium,a.output)
