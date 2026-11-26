"""Next.js EDS/MVP smoke: requires built frontend and isolated synthetic backend."""
import sys
from playwright.sync_api import sync_playwright, expect

ORIGIN = 'http://127.0.0.1:3000'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=sys.argv[1] if len(sys.argv)>1 else None)
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors, external = [], []
    page.on('pageerror',lambda error: errors.append(str(error)))
    def route_local(route):
        if route.request.url.startswith(ORIGIN+'/'):
            route.continue_()
        else:
            external.append(route.request.url)
            route.abort()
    page.route('**/*',route_local)
    page.goto(ORIGIN,wait_until='networkidle')
    expect(page.get_by_role('heading',name='CEO Command Center')).to_be_visible()
    nav=page.get_by_role('navigation',name='Ana navigasyon')
    expect(nav.locator('button,a')).to_have_count(13)
    theme=page.get_by_role('button',name='Açık tema')
    expect(theme).to_have_attribute('aria-pressed','false')
    theme.click()
    expect(page.locator('.eds-frame')).to_have_attribute('data-eds-theme','light')
    theme.click()
    expect(page.locator('.eds-frame')).to_have_attribute('data-eds-theme','dark')
    panel=page.get_by_role('region',name='Yerel MVP tanılama')
    panel.get_by_role('button',name='Sentetik backend oku').click()
    expect(panel.get_by_role('status')).to_contain_text('DENY / HOLD')
    expect(panel).to_contain_text('SQLITE_MEMORY_READBACK_ONLY')
    # Synthetic malformed response must never display an accepted grant.
    page.route('**/api/demo/mvp',lambda r:r.fulfill(status=200,content_type='application/json',body='{"dispatch_allowed":true}'))
    panel.get_by_role('button',name='Sentetik backend oku').click()
    expect(panel.get_by_role('status')).to_contain_text('HOLD')
    expect(panel.get_by_role('status')).to_contain_text('sözleşme uyumsuz')
    expect(panel).not_to_contain_text('SQLITE_MEMORY_READBACK_ONLY')
    page.unroute('**/api/demo/mvp')
    nav.get_by_role('link',name='Sanal Ofis').click()
    expect(page).to_have_url(ORIGIN+'/office')
    floors=page.get_by_role('group',name='Kat seçimi').get_by_role('button')
    expect(floors).to_have_count(2)
    floors.nth(1).click()
    expect(floors.nth(1)).to_have_attribute('aria-pressed','true')
    page.get_by_role('button',name='Liste',exact=True).click()
    expect(page.get_by_role('button',name='Liste',exact=True)).to_have_attribute('aria-pressed','true')
    assert not errors,errors
    assert not external,external
    print('PASS Next EDS, live local proxy, malformed response HOLD, office navigation and controls')
    browser.close()
