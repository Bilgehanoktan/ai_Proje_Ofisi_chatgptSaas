"""D0 native Next/Phaser browser smoke, called inside the reviewed W8 loopback stage."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def local_origin(url):
    u = urlsplit(url)
    if u.scheme != 'http' or u.hostname != '127.0.0.1' or not u.port or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('NATIVE_LOOPBACK_ONLY')
    return f'http://127.0.0.1:{u.port}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', required=True)
    parser.add_argument('--backend', required=True)
    parser.add_argument('--chromium', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    front, back = local_origin(args.frontend), local_origin(args.backend)
    if front == back or not args.chromium.is_file():
        raise ValueError('NATIVE_BROWSER_OR_PORT_HOLD')
    from playwright.sync_api import sync_playwright, expect
    args.output.mkdir(parents=True, exist_ok=False)
    checks, errors, external = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(args.chromium.resolve()))
        try:
            context = browser.new_context(viewport={'width':1440,'height':960}, reduced_motion='no-preference', service_workers='block')
            def intercept(route):
                url = urlsplit(route.request.url)
                if url.scheme in ('data', 'blob') or f'{url.scheme}://{url.netloc}' in (front, back):
                    route.continue_()
                else:
                    external.append(route.request.url)
                    route.abort()
            context.route('**/*', intercept)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(front + '/office/premium/native')
            scene = page.get_by_role('region', name='Native premium ofis')
            canvas = scene.locator('canvas')
            expect(canvas).to_be_visible(timeout=15000)
            expect(scene.locator('p.notice')).to_contain_text('ready', timeout=15000)
            expect(scene.locator('p.notice')).to_contain_text('JOIN_HOLD')
            expect(scene.get_by_text('Snapshot: EXACT_HISTORICAL_SAMPLE', exact=False)).to_be_visible()
            checks.append('native_canvas_and_d0_boundary')
            expect(scene.locator('[data-asset-mode]')).to_have_attribute('data-asset-mode','atlas',timeout=15000)
            checks.append('atlas_texture_marker')
            view = scene.locator('[data-camera-view]')
            scene.get_by_role('button',name='+',exact=True).click()
            page.wait_for_function('JSON.parse(document.querySelector("[data-camera-view]").dataset.cameraView).zoom > 1')
            before = json.loads(view.get_attribute('data-camera-view'))
            bounds = canvas.bounding_box()
            if not bounds:
                raise RuntimeError('NATIVE_CANVAS_BOUNDS_HOLD')
            page.mouse.click(bounds['x']+bounds['width']*875/1100,bounds['y']+bounds['height']*42/720)
            page.wait_for_function('(old)=>{let v=JSON.parse(document.querySelector("[data-camera-view]").dataset.cameraView);return Math.abs(v.x-old.x)>2||Math.abs(v.y-old.y)>2}',arg=before)
            checks.append('zoom_and_minimap')
            scene.get_by_role('button',name='engineer',exact=True).click()
            actor=scene.locator('[data-visual-role=engineer]')
            scene.get_by_role('button',name='Çalışma',exact=True).click()
            expect(actor).to_have_attribute('data-visual-mode','work',timeout=10000)
            scene.get_by_role('button',name='Toplantı',exact=True).click()
            expect(actor).to_have_attribute('data-visual-moving','true',timeout=5000)
            expect(actor).to_have_attribute('data-visual-mode','meeting',timeout=30000)
            checks.append('decorative_work_walk_meeting')
            page.screenshot(path=str(args.output/'native-floor1.png'),full_page=True)
            scene.get_by_role('button',name='Kat 2 · Rezerv',exact=True).click()
            expect(scene.locator('[data-visual-role]')).to_have_count(0)
            expect(scene.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled()
            scene.get_by_role('button',name='Kat 1',exact=True).click()
            expect(scene.locator('[data-visual-role]')).to_have_count(4)
            checks.append('passive_floor_no_occupants')
            scene.get_by_role('button',name='Karakterleri sıfırla').click()
            expect(actor).to_have_attribute('data-visual-mode','idle')
            page.emulate_media(reduced_motion='reduce')
            expect(scene.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled()
            checks.append('reset_and_reduced_motion')
            page.reload()
            expect(canvas).to_be_visible(timeout=15000)
            expect(scene.locator('p.notice')).to_contain_text('ready', timeout=15000)
            expect(scene.locator('[data-asset-mode]')).to_have_attribute('data-asset-mode','atlas',timeout=15000)
            expect(scene.get_by_role('button',name='Çalışma',exact=True)).to_be_disabled()
            checks.append('reload_atlas_reduced_motion')
            if errors or external:
                raise RuntimeError(f'NATIVE_ERRORS_HOLD: {errors!r}, external={len(external)}')
            checks.append('no_page_errors_or_nonlocal_requests')
            (args.output/'NATIVE_EVIDENCE.json').write_text(json.dumps({'status':'PASS_SELECTED_NATIVE_SMOKE','checks':checks,'browser':browser.version,'office_v0':'JOIN_HOLD','manual_visual_review':'NOT_RUN','independent':'HOLD'},indent=2)+'\n',encoding='utf-8')
            print(f'PASS {len(checks)} native smoke groups; manual visual acceptance remains open')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
