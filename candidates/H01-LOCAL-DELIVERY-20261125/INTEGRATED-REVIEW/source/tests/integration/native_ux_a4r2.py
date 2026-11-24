"""Actual D0 hybrid browser diagnostics, only inside reviewed W8 loopback smoke."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit


def local_origin(url):
    u = urlsplit(url)
    if u.scheme != 'http' or u.hostname != '127.0.0.1' or not u.port or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('HYBRID_LOOPBACK_ONLY')
    return f'http://127.0.0.1:{u.port}'


def frame_metrics(values):
    if not isinstance(values, list) or not 30 <= len(values) <= 120 or any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError('HYBRID_FRAME_SAMPLE_HOLD')
    ordered = sorted(values)
    mean = sum(values) / len(values)
    return {'samples': len(values), 'mean_delta_ms': mean, 'p95_delta_ms': ordered[math.ceil(.95*len(values))-1], 'max_delta_ms': max(values), 'estimated_update_hz': 1000/mean, 'scope': 'Phaser scene update delta; not GPU or raw display FPS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', required=True)
    parser.add_argument('--backend', required=True)
    parser.add_argument('--chromium', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    front, back = local_origin(args.frontend), local_origin(args.backend)
    if front == back or not args.chromium.is_file():
        raise ValueError('HYBRID_BROWSER_OR_PORT_HOLD')
    from playwright.sync_api import sync_playwright, expect
    args.output.mkdir(parents=True, exist_ok=False)
    checks, errors, external, samples, captures = [], [], [], {}, {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(args.chromium.resolve()))
        try:
            def open_scene(viewport, reduced):
                context = browser.new_context(viewport=viewport, reduced_motion=reduced, service_workers='block')
                def intercept(route):
                    u = urlsplit(route.request.url)
                    if u.scheme in ('data', 'blob') or f'{u.scheme}://{u.netloc}' in (front, back):
                        route.continue_()
                    else:
                        external.append(u.hostname)
                        route.abort()
                context.route('**/*', intercept)
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(front+'/office/premium/hybrid')
                scene = page.get_by_role('region', name='Hibrit Premium Ofis')
                status = scene.locator('[data-hybrid-status]')
                expect(scene.locator('canvas')).to_have_count(1, timeout=15000)
                expect(scene.locator('canvas')).to_be_visible(timeout=15000)
                expect(status).to_have_attribute('data-hybrid-status', 'ready', timeout=15000)
                expect(status).to_contain_text('JOIN_HOLD')
                expect(status).to_have_attribute('data-asset-mode', 'atlas')
                expect(scene.locator('[data-visual-id]')).to_have_count(4)
                ids = scene.locator('[data-visual-id]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.visualId)')
                if set(ids) != {'d0-visual-e','d0-visual-o','d0-visual-q','d0-visual-r'}:
                    raise ValueError('HYBRID_VISUAL_ID_HOLD')
                page.wait_for_function("['webgl','canvas'].includes(document.querySelector('[data-hybrid-status]').dataset.renderer)")
                box = scene.locator('canvas').bounding_box()
                if not box or box['width'] <= 0 or box['height'] <= 0 or box['x'] < -1 or box['x']+box['width'] > viewport['width']+1:
                    raise ValueError('HYBRID_CANVAS_FIT_HOLD')
                return context, page, scene, status

            def capture(page, name):
                path = args.output/(name+'.png')
                page.screenshot(path=str(path), full_page=True)
                captures[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

            def read_camera(status):
                return json.loads(status.get_attribute('data-camera-view'))

            def read_samples(page, status):
                page.wait_for_function("JSON.parse(document.querySelector('[data-frame-deltas]').dataset.frameDeltas).length >= 30", timeout=15000)
                return {**frame_metrics(json.loads(status.get_attribute('data-frame-deltas'))), 'renderer': status.get_attribute('data-renderer')}

            context, page, scene, status = open_scene({'width':1440,'height':960}, 'no-preference')
            checks.append('desktop_actual_canvas_atlas_and_D0_ids')
            page.wait_for_function("JSON.parse(document.querySelector('[data-camera-view]').dataset.cameraView).fit > 0")
            initial = read_camera(status)
            if abs(initial['zoom']-initial['fit']) > .001:
                raise ValueError('HYBRID_INITIAL_FIT_HOLD')
            capture(page,'desktop-fit')
            scene.get_by_role('button',name='+',exact=True).click()
            page.wait_for_function("old=>JSON.parse(document.querySelector('[data-camera-view]').dataset.cameraView).zoom > old",arg=initial['zoom'])
            scene.get_by_role('button',name='engineer · d0-visual-e',exact=True).click()
            scene.get_by_role('button',name='Odakla',exact=True).click()
            page.wait_for_function("old=>{const v=JSON.parse(document.querySelector('[data-camera-view]').dataset.cameraView);return Math.abs(v.x-old.x)>2||Math.abs(v.y-old.y)>2}",arg=initial)
            capture(page,'desktop-focus')
            before = read_camera(status)
            bounds = scene.locator('canvas').bounding_box()
            page.mouse.click(bounds['x']+bounds['width']*875/1100,bounds['y']+bounds['height']*22/720)
            page.wait_for_function("old=>{const v=JSON.parse(document.querySelector('[data-camera-view]').dataset.cameraView);return Math.abs(v.x-old.x)>2||Math.abs(v.y-old.y)>2}",arg=before)
            scene.get_by_role('button',name='Tüm ofis',exact=True).click()
            page.wait_for_function("()=>{const v=JSON.parse(document.querySelector('[data-camera-view]').dataset.cameraView);return Math.abs(v.zoom-v.fit)<.001}")
            checks.append('camera_zoom_focus_minimap_fit')
            samples['desktop_idle'] = read_samples(page,status)
            actor = scene.locator('[data-visual-id=d0-visual-e]')
            traffic = scene.locator('[data-traffic-status]')
            expect(actor).to_have_attribute('data-cell','39,7')
            scene.get_by_role('button',name='Briefing alanı',exact=True).click()
            expect(actor).to_have_attribute('data-moving','true',timeout=10000)
            scene.get_by_role('button',name='Duraklat',exact=True).click()
            page.wait_for_timeout(400)
            frozen = (traffic.get_attribute('data-traffic-tick'),actor.get_attribute('data-position'))
            page.wait_for_timeout(650)
            if frozen != (traffic.get_attribute('data-traffic-tick'),actor.get_attribute('data-position')):
                raise ValueError('HYBRID_PAUSE_HOLD')
            capture(page,'desktop-paused')
            scene.get_by_role('button',name='Devam',exact=True).click()
            page.wait_for_timeout(1500)
            samples['desktop_moving_window'] = read_samples(page,status)
            expect(actor).to_have_attribute('data-cell','24,23',timeout=45000)
            expect(traffic).to_have_attribute('data-traffic-status','READY',timeout=10000)
            capture(page,'desktop-briefing')
            scene.get_by_role('button',name='İstasyona dön',exact=True).click()
            expect(actor).to_have_attribute('data-at-station','true',timeout=45000)
            expect(traffic).to_have_attribute('data-traffic-status','READY',timeout=10000)
            checks.append('accepted_movement_pause_resume_and_return')
            page.emulate_media(reduced_motion='reduce')
            expect(scene.get_by_role('button',name='Briefing alanı',exact=True)).to_be_disabled()
            page.reload()
            expect(status).to_have_attribute('data-hybrid-status','ready',timeout=15000)
            expect(scene.locator('canvas')).to_have_count(1)
            expect(scene.get_by_role('button',name='Briefing alanı',exact=True)).to_be_disabled()
            page.get_by_role('link',name='← Önceki native ofis').click()
            expect(page.get_by_role('region',name='Native premium ofis')).to_be_visible(timeout=15000)
            expect(scene).to_have_count(0)
            checks.append('reduced_motion_reload_and_route_departure')
            context.close()
            mobile, mp, ms, mstatus = open_scene({'width':390,'height':844}, 'reduce')
            expect(ms.get_by_role('button',name='Briefing alanı',exact=True)).to_be_disabled()
            capture(mp,'mobile-fit')
            samples['mobile_viewport_idle'] = read_samples(mp,mstatus)
            checks.append('mobile_viewport_canvas_and_reduced_motion')
            mobile.close()
            if errors or external:
                raise RuntimeError(f'HYBRID_PAGE_ERROR_HOLD: {len(errors)} page errors, {len(external)} nonlocal requests')
            checks.append('no_page_errors_or_nonlocal_requests')
            evidence = {'status':'PASS_SELECTED_HYBRID_NATIVE','checks':checks,'browser':browser.version,'captures_sha256':captures,'frame_samples':samples,'office_v0':'JOIN_HOLD','manual_visual_review':'NOT_RUN','gpu_timing':'NOT_RUN','fallback_forced':'NOT_RUN','independent':'HOLD'}
            (args.output/'HYBRID_NATIVE_EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
            print('PASS',len(checks),'hybrid native groups; manual art, GPU and independent acceptance open')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
