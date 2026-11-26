from pathlib import Path
import hashlib, os, subprocess, sys, tempfile, time, urllib.request
from playwright.sync_api import sync_playwright, expect
stage=Path('core-0227-e1').resolve()
back=stage/'product/ai-company-os-backend'; front=stage/'product/ai-company-os-frontend'
sys.path[:0]=[str(back),str(back/'tests')]
from test_lifecycle_db_http_0225 import write_fixture
origin='http://127.0.0.1:17500'; backend='http://127.0.0.1:17501'
allow={'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','SYSTEMDRIVE'}
with tempfile.TemporaryDirectory(prefix='e4-',dir=stage) as tmp:
 db=Path(tmp)/'lifecycle-prefix.d0.sqlite'; write_fixture(db,3); initial=hashlib.sha256(db.read_bytes()).digest()
 env={k:v for k,v in os.environ.items() if k.upper() in allow}
 env.update(AICOS_D0_LIFECYCLE_PREFIX_DB=str(db), AICOS_D0_BACKEND_PORT='17501',NEXT_TELEMETRY_DISABLED='1', PYTHONDONTWRITEBYTECODE='1',NO_PROXY='127.0.0.1',PYTHONUTF8='1')
 procs=[]
 try:
  for command,cwd,url in (([sys.executable,'-B','-m','uvicorn','app.main:app','--host','127.0.0.1','--port','17501'],back,backend+'/demo/v1/lifecycle/shared-snapshot'),(['node','node_modules/next/dist/bin/next','start','-H','127.0.0.1','-p','17500'],front,origin+'/')):
   proc=subprocess.Popen(command,cwd=cwd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(proc)
   for _ in range(35):
    if proc.poll() is not None: raise RuntimeError('server exited')
    try:
     with urllib.request.urlopen(url,timeout=2) as response: assert response.status==200; break
    except OSError:time.sleep(1)
   else:raise RuntimeError('server did not become ready')
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'); page=browser.new_page()
   errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def guard(route):
    if route.request.url.startswith((origin+'/', 'data:', 'blob:'+origin+'/')): route.continue_()
    else: external.append(route.request.url);route.abort()
   page.route('**/*',guard);page.goto(origin+'/',wait_until='networkidle')
   ceo=page.get_by_role('region',name='CEO ortak tarihsel oturumu'); office=page.get_by_role('region',name='Office ortak tarihsel oturumu'); studio=page.get_by_role('region',name='Studio kimlik ve kanıt bağlamı').first
   ceo.get_by_role('button',name='Snapshot yeniden oku').click()
   for panel in (ceo,office): expect(panel.get_by_role('status')).to_contain_text('Tarihsel replay tamamlandı');expect(panel).to_contain_text('RUNNING')
   expect(studio).to_contain_text('Tarihsel oturum mevcut');expect(studio).to_contain_text('JOIN HOLD')
   studio.get_by_role('button',name='Backend planını oku').click();expect(studio).to_contain_text('Backend derleyici yanıtı sabit planla eşleşti')
   page.route('**/api/demo/plan',lambda r:r.fulfill(status=200,content_type='application/json',body='{"digest":"wrong"}'))
   studio.get_by_role('button',name='Backend planını oku').click();expect(studio).to_contain_text('Backend planı HOLD');page.unroute('**/api/demo/plan')
   replay=page.request.get(origin+'/api/demo/shared-snapshot',headers={'Last-Event-ID':'1'});assert replay.status==503
   page.route('**/api/demo/shared-snapshot',lambda r:r.fulfill(status=200,content_type='text/event-stream',body='event: reset\ndata: {}\n\n'))
   ceo.get_by_role('button',name='Snapshot yeniden oku').click()
   for panel in (ceo,office):expect(panel.get_by_role('status')).to_contain_text('Geçersiz');expect(panel).not_to_contain_text('RUNNING')
   page.unroute('**/api/demo/shared-snapshot');office.get_by_role('button',name='Snapshot yeniden oku').click();expect(ceo.get_by_role('status')).to_contain_text('Tarihsel replay tamamlandı')
   page.get_by_role('link',name='Sanal Ofis',exact=True).click();expect(page).to_have_url(origin+'/office');expect(office).to_contain_text('RUNNING')
   assert not errors and not external,'browser error or external request'; browser.close()
  assert hashlib.sha256(db.read_bytes()).digest()==initial
  print('PASS real D0 SQLite, HTTP/SSE, CEO/Office/Studio, plan mismatch, invalid replay, resync, route continuity and read-only hash')
 finally:
  for proc in reversed(procs):
   proc.terminate()
   try:proc.wait(timeout=8)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
