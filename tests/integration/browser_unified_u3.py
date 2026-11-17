"""Actual U3 product browser acceptance; no stub API, no production endpoints."""
import argparse
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frontend-port', required=True, type=int)
    p.add_argument('--chromium', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if not 1024 <= a.frontend_port <= 49151 or not a.chromium.is_file():
        raise ValueError('U3_BROWSER_SCOPE_HOLD')
    a.output.mkdir(parents=True, exist_ok=False)
    origin = f'http://127.0.0.1:{a.frontend_port}'
    url = origin+'/api/demo/shared-snapshot'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(a.chromium))
        page = browser.new_page(viewport={'width':1440,'height':900}, reduced_motion='reduce')
        errors, external, reads = [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: reads.append(request.url) if request.url == url else None)
        def route_local(route):
            target = route.request.url
            if target.startswith(origin+'/') or target.startswith(('data:', 'blob:'+origin+'/')):
                route.continue_()
            else:
                external.append(target)
                route.abort()
        page.route('**/*', route_local)
        page.goto(origin+'/', wait_until='networkidle')
        page.evaluate("window.__u3SessionSentinel = 'same-document'")
        nav = page.get_by_role('navigation', name='Ana navigasyon')
        ceo = page.get_by_role('region', name='CEO ortak tarihsel oturumu')
        def read(panel):
            with page.expect_response(lambda r: r.url == url) as response:
                panel.get_by_role('button', name='Snapshot yeniden oku').click()
            r = response.value
            assert r.status == 200 and r.headers.get('cache-control') == 'no-store'
            lines = r.text().splitlines()
            assert lines[0] == 'event: snapshot' and lines[1].startswith('data: ')
            snap = json.loads(lines[1][6:])
            assert snap['project_id'] is None and snap['world_id'] is None
            assert snap['prefix']['dispatch_allowed'] is False and snap['prefix']['geometry_join'] == 'HOLD'
            assert re.fullmatch(r'[a-f0-9]{64}', snap['digest'])
            expect(panel).to_contain_text(snap['digest'])
            return snap['digest']
        digest = read(ceo)
        page.screenshot(path=str(a.output/'01-ceo.png'), full_page=True)
        nav.get_by_role('button', name='AI Çalışanlar', exact=True).click()
        directory = page.get_by_role('region', name='Agent Studio')
        directory.locator('button[aria-pressed]').filter(has_text=re.compile('Rol şablonu|REZERV')).first.click()
        agent = page.get_by_role('region', name='Studio kimlik ve kanıt bağlamı')
        expect(agent).to_contain_text(digest)
        expect(agent).to_contain_text('JOIN HOLD')
        page.screenshot(path=str(a.output/'02-agent.png'), full_page=True)
        nav.get_by_role('button', name='İş ve Denetim', exact=True).click()
        sections = page.get_by_role('group', name='İş ve Denetim bölümleri seçimi')
        project = page.get_by_role('region', name='Proje yönetim merkezi').get_by_role('region', name='Studio kimlik ve kanıt bağlamı')
        expect(project).to_contain_text(digest)
        sections.get_by_role('button', name='Workflow Studio', exact=False).click()
        workflow = page.get_by_role('region', name='Yerel workflow taslak editörü')
        context = workflow.get_by_role('region', name='Studio kimlik ve kanıt bağlamı')
        expect(context).to_contain_text(digest)
        expect(context).to_contain_text('PLAN_REVISION_MISMATCH')
        page.screenshot(path=str(a.output/'03-workflow.png'), full_page=True)
        assert len(reads) == 1, 'unexpected extra shared read'
        context.get_by_role('button', name='Ortak geçmişi temizle').click()
        expect(context).not_to_contain_text(digest)
        nav.get_by_role('button', name='Genel Bakış', exact=True).click()
        expect(ceo).not_to_contain_text(digest)
        digest = read(ceo)
        nav.get_by_role('link', name='Sanal Ofis', exact=True).click()
        expect(page).to_have_url(origin+'/office')
        office = page.get_by_role('region', name='Office ortak tarihsel oturumu')
        expect(office).to_contain_text(digest)
        page.get_by_role('link', name='Birleşik ofis · D0 ↗', exact=True).click()
        expect(page).to_have_url(origin+'/office/premium/unified')
        expect(office).to_contain_text(digest)
        assert page.evaluate("window.__u3SessionSentinel") == 'same-document'
        assert len(reads) == 2, 'navigation must not trigger shared read'
        preview = page.get_by_role('region', name='Sentetik çok katlı ofis')
        expect(preview.get_by_role('status')).to_contain_text('4 sentetik rol')
        preview.get_by_role('button', name='Kat 3 · Taslak').click()
        expect(preview.get_by_role('status')).to_contain_text('0 sentetik rol')
        expect(preview.locator('img')).to_have_js_property('complete', True)
        assert preview.locator('img').evaluate('(img) => img.naturalWidth > 0')
        page.screenshot(path=str(a.output/'04-office.png'), full_page=True)
        # Real browser timer: re-read then wait for TTL rather than simulating time.
        read(office)
        expect(office.get_by_role('status')).to_have_attribute('data-phase', 'hold', timeout=35000)
        expect(office).not_to_contain_text(digest)
        expect(preview.get_by_role('status')).to_contain_text('0 sentetik rol')
        assert len(reads) == 3 and not external and not errors, (reads, external, errors)
        page.screenshot(path=str(a.output/'05-expired.png'), full_page=True)
        browser.close()
    (a.output/'U3_BROWSER_REPORT.json').write_text(json.dumps({'status':'PASS','shared_reads':len(reads),'actual_browser':True,'same_document':True,'screenshots':5,'join':'HOLD'}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
