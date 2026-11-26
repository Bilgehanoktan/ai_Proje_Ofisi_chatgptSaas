"""Real Chromium smoke on pinned historical offline HTML, not the Next.js build."""
import hashlib
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

html = Path(sys.argv[1]).read_bytes()
assert hashlib.sha1(f'blob {len(html)}\0'.encode()+html).hexdigest() == '1b7b4ce55553711beccb686174040427d926b5a0'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=sys.argv[2] if len(sys.argv)>2 else None)
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors = []
    requests = []
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.route('**/*',lambda route:(requests.append(route.request.url),route.abort()))
    page.set_content(html.decode('utf-8'))
    def button(name): return page.get_by_role('button',name=name,exact=True)
    assert page.locator('h1').inner_text() == 'CEO Command Center'
    assert page.locator('aside nav button').count() == 13
    print('PASS initial dashboard and 13 navigation entries')
    assert 'Admission: DENY' in page.locator('body').inner_text()
    assert 'Dispatch=false · Release=false' in page.locator('body').inner_text()
    print('PASS deny/no-release presentation')
    button('Kat 2').click()
    assert 'Bu katta istasyon yok.' in page.locator('body').inner_text()
    button('Kat 1').click()
    assert '4 rezerv istasyon' in page.locator('body').inner_text()
    print('PASS floor switch and empty reserve')
    button('Gap senaryosu').click()
    for _ in range(3): button('İleri').click()
    assert 'RESYNC_REQUIRED' in page.locator('body').inner_text()
    button('Sıfırla').click()
    assert 'RESYNC_REQUIRED' not in page.locator('body').inner_text()
    assert 'Görsel sıra: 0' in page.locator('body').inner_text()
    print('PASS event gap and reset')
    page.get_by_role('button',name='Güvenlik').click()
    assert page.locator('h1').inner_text() == 'Güvenlik'
    print('PASS security navigation')
    page.get_by_role('button',name='Genel Bakış').click()
    assert page.locator('h1').inner_text() == 'CEO Command Center'
    print('PASS return to dashboard')
    for width in (375,768,1440):
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    print('PASS responsive horizontal overflow at 375/768/1440')
    assert not errors,errors
    assert not requests,requests
    print('PASS no JavaScript errors or network requests')
    browser.close()
